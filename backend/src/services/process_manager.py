"""
Process lifecycle management for subprocess tracking and cleanup.

AICODE-NOTE: This module implements FR-016.1 and FR-016.2 - preventing zombie processes
when SSE clients disconnect. Uses SIGTERM → SIGKILL pattern from research.md R2.
"""

import asyncio
import signal
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from loguru import logger


@dataclass
class ProcessTracker:
    """
    Track metadata for a running subprocess.

    AICODE-NOTE: Dataclass for T013 - stores process reference and metadata.
    Used by ProcessManager to maintain registry of active processes.
    """
    request_id: str
    process: asyncio.subprocess.Process
    started_at: float


class ProcessManager:
    """
    Manage subprocess lifecycle with automatic cleanup on disconnect.

    AICODE-NOTE: Implements T014-T016 - core process management functionality.
    Critical for FR-016.2 (zombie prevention) and SC-012 (cleanup within 5s).
    """

    def __init__(self):
        """Initialize ProcessManager with empty process registry."""
        # AICODE-NOTE: T014 - active_processes dict tracks all running subprocesses
        self.active_processes: dict[str, ProcessTracker] = {}
        logger.info("ProcessManager initialized")

    async def cleanup_process(
        self,
        process: asyncio.subprocess.Process,
        timeout: float = 3.0
    ) -> None:
        """
        Clean up a subprocess using SIGTERM → SIGKILL pattern.

        AICODE-NOTE: T015 - implements graceful shutdown with fallback to force kill.
        Pattern from research.md R2: SIGTERM → wait 3s → SIGKILL if needed.

        Args:
            process: The subprocess to clean up
            timeout: Seconds to wait for graceful shutdown before SIGKILL

        Returns:
            None
        """
        # AICODE-NOTE: Skip cleanup if process already finished
        if process.returncode is not None:
            logger.debug("Process already finished, skipping cleanup")
            return

        try:
            # AICODE-NOTE: Send SIGTERM for graceful shutdown
            logger.info(f"Sending SIGTERM to process {process.pid}")
            process.send_signal(signal.SIGTERM)

            # AICODE-NOTE: Wait for graceful shutdown with timeout
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout)
                logger.success(f"Process {process.pid} terminated gracefully")
            except asyncio.TimeoutError:
                # AICODE-NOTE: SIGTERM failed, force kill with SIGKILL
                logger.warning(
                    f"Process {process.pid} did not respond to SIGTERM "
                    f"after {timeout}s, sending SIGKILL"
                )
                process.kill()
                await process.wait()
                logger.info(f"Process {process.pid} killed forcefully")

        except ProcessLookupError:
            # AICODE-NOTE: Process already terminated (race condition)
            logger.debug("Process already terminated during cleanup")

    @asynccontextmanager
    async def track_process(
        self,
        request_id: str,
        process: asyncio.subprocess.Process
    ) -> AsyncIterator[ProcessTracker]:
        """
        Context manager for automatic process tracking and cleanup.

        AICODE-NOTE: T016 - ensures cleanup happens on disconnect or exception.
        Used by SSE endpoint to guarantee cleanup on all exit paths (FR-016.2).

        Args:
            request_id: Unique identifier for this request
            process: The subprocess to track

        Yields:
            ProcessTracker instance for this process

        Example:
            async with manager.track_process(request_id, process) as tracker:
                # Process is tracked in registry
                async for line in process.stdout:
                    yield line
            # Cleanup happens automatically here
        """
        # AICODE-NOTE: Create tracker and add to registry
        tracker = ProcessTracker(
            request_id=request_id,
            process=process,
            started_at=time.time()
        )
        self.active_processes[request_id] = tracker
        logger.info(f"Tracking process {process.pid} for request {request_id}")

        try:
            # AICODE-NOTE: Yield control to caller (SSE streaming loop)
            yield tracker

        finally:
            # AICODE-NOTE: Cleanup happens on ALL exit paths (normal, exception, disconnect)
            logger.info(f"Cleaning up process {process.pid} for request {request_id}")

            # AICODE-NOTE: Remove from registry first
            if request_id in self.active_processes:
                del self.active_processes[request_id]

            # AICODE-NOTE: Terminate process if still running
            await self.cleanup_process(process)

            logger.success(f"Process {process.pid} cleanup complete")
