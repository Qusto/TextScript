"""
SSE streaming endpoint for article generation.

AICODE-NOTE: Implements T017-T020 - FastAPI router with SSE streaming.
This endpoint spawns a subprocess, streams stdout as SSE, and detects client disconnect.
"""

import asyncio
import sys
import uuid
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from loguru import logger

from src.services.process_manager import ProcessManager

# AICODE-NOTE: T017 - Create FastAPI router for generate endpoint
router = APIRouter()

# AICODE-NOTE: Global ProcessManager instance for tracking all active processes
process_manager = ProcessManager()


async def generate_article_stream(
    request: Request,
    topic: str,
    urls: str,
    research: bool
) -> AsyncIterator[str]:
    """
    Stream article generation output as Server-Sent Events.

    AICODE-NOTE: T018-T020 - Core SSE streaming implementation.
    Spawns subprocess, streams stdout, detects disconnect.

    Args:
        request: FastAPI request object for disconnect detection
        topic: Article topic
        urls: Source URLs (newline or comma separated)
        research: Whether to enable research mode

    Yields:
        SSE formatted strings (data: messages, events)
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Starting generation request {request_id} for topic: {topic}")

    # AICODE-NOTE: T018 - Spawn subprocess using asyncio.create_subprocess_exec
    # For testing, use mock_script.py. In production, use real article script.
    # TODO: Replace with actual article script command

    # AICODE-NOTE: Determine script path (use mock for now)
    mock_script = Path(__file__).parent.parent.parent / "tests" / "mock_script.py"

    try:
        # AICODE-NOTE: Create subprocess with pipe for stdout/stderr
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(mock_script),  # AICODE-TODO: Replace with real script
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        logger.info(f"Spawned process {process.pid} for request {request_id}")

        # AICODE-NOTE: T016 - Track process for automatic cleanup on disconnect
        async with process_manager.track_process(request_id, process):

            # AICODE-NOTE: T019 - Stream stdout line-by-line as SSE messages
            # T020 - Check disconnect on every iteration
            while not await request.is_disconnected():
                # AICODE-NOTE: Read one line from subprocess stdout
                line = await process.stdout.readline()

                # AICODE-NOTE: Break if process ended (empty line indicates EOF)
                if not line:
                    break

                # AICODE-NOTE: Decode and strip whitespace
                decoded_line = line.decode('utf-8').strip()

                # AICODE-NOTE: Send as SSE "data:" message (default event type)
                # SSE format: "data: <content>\n\n"
                yield f"data: {decoded_line}\n\n"

                logger.debug(f"Streamed line: {decoded_line}")

            # AICODE-NOTE: Wait for process to complete
            return_code = await process.wait()

            # AICODE-NOTE: T020 - Check if client disconnected during streaming
            if await request.is_disconnected():
                logger.warning(f"Client disconnected for request {request_id}")
                # AICODE-NOTE: Cleanup handled by context manager
                return

            # AICODE-NOTE: Handle process exit status
            if return_code != 0:
                # AICODE-NOTE: Send error event for non-zero exit
                stderr = await process.stderr.read()
                error_msg = stderr.decode('utf-8').strip() if stderr else "Unknown error"
                logger.error(f"Process failed with code {return_code}: {error_msg}")

                # AICODE-NOTE: Send custom SSE error event
                yield f"event: error\ndata: Process failed: {error_msg}\n\n"
            else:
                # AICODE-NOTE: Success - send result and close events
                logger.success(f"Generation completed for request {request_id}")

                # AICODE-NOTE: T019 - Send custom 'result' event
                # TODO: Parse actual article from stdout (for now, mock)
                yield f"event: result\ndata: Article generated successfully\n\n"

            # AICODE-NOTE: T019 - Send close event to signal stream end
            yield f"event: close\ndata: done\n\n"

    except Exception as e:
        # AICODE-NOTE: Handle unexpected errors
        logger.exception(f"Error during generation for request {request_id}")
        yield f"event: error\ndata: {str(e)}\n\n"
        yield f"event: close\ndata: done\n\n"


@router.get("/generate")
async def stream_generation(
    request: Request,
    topic: str = Query(..., description="Article topic"),
    urls: str = Query(..., description="Source URLs (newline or comma separated)"),
    research: bool = Query(False, description="Enable research mode")
) -> StreamingResponse:
    """
    SSE endpoint for real-time article generation streaming.

    AICODE-NOTE: T017 - FastAPI router endpoint with SSE streaming response.
    Validates parameters, returns StreamingResponse with text/event-stream.

    Args:
        request: FastAPI request object
        topic: Article topic (required)
        urls: Source URLs (required)
        research: Research flag (optional, default False)

    Returns:
        StreamingResponse with SSE stream
    """
    logger.info(f"Received generation request: topic={topic}, research={research}")

    # AICODE-NOTE: Return StreamingResponse with SSE media type
    return StreamingResponse(
        generate_article_stream(request, topic, urls, research),
        media_type="text/event-stream",
        headers={
            # AICODE-NOTE: Required headers for SSE
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # AICODE-NOTE: Allow CORS for frontend (adjust in production)
            "Access-Control-Allow-Origin": "*",
        }
    )
