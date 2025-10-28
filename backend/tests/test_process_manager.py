"""
Tests for ProcessManager - subprocess lifecycle management.

AICODE-NOTE: Test-first approach for T013-T016 (ProcessManager implementation).
These tests MUST fail initially (red phase) before implementation.
"""

import asyncio
import signal
import sys
from pathlib import Path

import pytest

from src.services.process_manager import ProcessManager, ProcessTracker


# AICODE-NOTE: Test data class first (T013)
class TestProcessTracker:
    """Test ProcessTracker dataclass."""

    def test_process_tracker_initialization(self):
        """Test ProcessTracker can be initialized with required fields."""
        # AICODE-NOTE: Minimal test - just verify dataclass structure
        process = None  # Will be a real process in integration
        tracker = ProcessTracker(
            request_id="test-123",
            process=process,
            started_at=0.0
        )

        assert tracker.request_id == "test-123"
        assert tracker.process is None
        assert tracker.started_at == 0.0


# AICODE-NOTE: Test ProcessManager core functionality (T014-T016)
class TestProcessManager:
    """Test ProcessManager class for subprocess tracking and cleanup."""

    @pytest.fixture
    def manager(self):
        """Create ProcessManager instance for each test."""
        return ProcessManager()

    @pytest.mark.asyncio
    async def test_active_processes_dict_tracking(self, manager):
        """Test ProcessManager maintains active_processes dict (T014)."""
        # AICODE-NOTE: Verify manager initializes with empty dict
        assert hasattr(manager, 'active_processes')
        assert isinstance(manager.active_processes, dict)
        assert len(manager.active_processes) == 0

    @pytest.mark.asyncio
    async def test_cleanup_process_sigterm_success(self, manager):
        """Test cleanup_process sends SIGTERM and waits for graceful shutdown (T015)."""
        # AICODE-NOTE: Start a long-running process that responds to SIGTERM
        mock_script = Path(__file__).parent / "mock_script.py"
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(mock_script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # AICODE-NOTE: Wait a bit to ensure process is running
        await asyncio.sleep(0.05)
        assert process.returncode is None

        # AICODE-NOTE: Test cleanup - should send SIGTERM and wait
        await manager.cleanup_process(process)

        # AICODE-NOTE: Process should be terminated (returncode != None)
        # SIGTERM results in negative return code (-15 on Unix)
        assert process.returncode is not None

    @pytest.mark.asyncio
    async def test_cleanup_process_sigkill_on_timeout(self, manager):
        """Test cleanup_process sends SIGKILL if SIGTERM timeout exceeds 3s (T015)."""
        # AICODE-NOTE: Create a process that ignores SIGTERM
        # Use sleep command which doesn't respond to SIGTERM immediately
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            "import time; import signal; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await asyncio.sleep(0.05)
        assert process.returncode is None

        # AICODE-NOTE: cleanup_process should timeout and SIGKILL
        # Using shorter timeout for test speed
        await manager.cleanup_process(process, timeout=0.1)

        # AICODE-NOTE: Process should be killed forcefully
        assert process.returncode is not None
        # SIGKILL results in -9 exit code on Unix
        assert process.returncode < 0  # Negative indicates signal termination

    @pytest.mark.asyncio
    async def test_track_process_context_manager(self, manager):
        """Test track_process context manager adds and removes from registry (T016)."""
        # AICODE-NOTE: Start a simple process
        mock_script = Path(__file__).parent / "mock_script.py"
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(mock_script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        request_id = "test-request-123"

        # AICODE-NOTE: Before tracking, registry should be empty
        assert request_id not in manager.active_processes

        # AICODE-NOTE: Track process using context manager
        async with manager.track_process(request_id, process):
            # AICODE-NOTE: Process should be in registry during context
            assert request_id in manager.active_processes
            assert manager.active_processes[request_id].process == process

        # AICODE-NOTE: After context exit, process should be cleaned up
        assert request_id not in manager.active_processes
        # Process should be terminated
        assert process.returncode is not None

    @pytest.mark.asyncio
    async def test_track_process_cleanup_on_exception(self, manager):
        """Test track_process cleans up even if exception occurs (T016)."""
        # AICODE-NOTE: Verify cleanup happens on exception path
        mock_script = Path(__file__).parent / "mock_script.py"
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(mock_script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        request_id = "test-exception-123"

        # AICODE-NOTE: Raise exception inside context manager
        with pytest.raises(RuntimeError):
            async with manager.track_process(request_id, process):
                assert request_id in manager.active_processes
                raise RuntimeError("Simulated error")

        # AICODE-NOTE: Cleanup should still happen
        assert request_id not in manager.active_processes
        assert process.returncode is not None

    @pytest.mark.asyncio
    async def test_track_process_no_cleanup_if_already_finished(self, manager):
        """Test track_process handles already-finished processes gracefully (T016)."""
        # AICODE-NOTE: Start and immediately finish a process
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            "print('done')",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for process to finish
        await process.wait()
        assert process.returncode == 0

        request_id = "test-finished-123"

        # AICODE-NOTE: Tracking finished process should not error
        async with manager.track_process(request_id, process):
            assert request_id in manager.active_processes

        # AICODE-NOTE: Should remove from registry without issues
        assert request_id not in manager.active_processes
