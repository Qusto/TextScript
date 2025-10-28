"""
SSE streaming endpoint for article generation.

AICODE-NOTE: Implements T017-T020 - FastAPI router with SSE streaming.
This endpoint spawns a subprocess, streams stdout as SSE, and detects client disconnect.

AICODE-NOTE: T030-T032 - Enhanced with:
- T030: Read output.txt for result event
- T031: Proper close event emission
- T032: Pydantic input validation
"""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import ValidationError

from src.models.request import GenerateArticleRequest
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

    # AICODE-NOTE: T073 - Set timeout for long-running generations (10 minutes)
    # Prevents resource waste from stuck processes
    GENERATION_TIMEOUT = 600  # 10 minutes in seconds

    # AICODE-NOTE: T018 - Spawn subprocess using asyncio.create_subprocess_exec
    # For testing, use mock_script.py. In production, use real article script.
    # TODO: Replace with actual article script command

    # AICODE-NOTE: Determine script path (use mock for now)
    mock_script = Path(__file__).parent.parent.parent / "tests" / "mock_script.py"

    # AICODE-NOTE: T041 - Prepare environment variables for subprocess
    # Pass research flag to the script via RESEARCH_ENABLED env var
    subprocess_env = {
        **dict(os.environ),  # Inherit parent environment
        "RESEARCH_ENABLED": "true" if research else "false",
    }

    try:
        # AICODE-NOTE: Create subprocess with pipe for stdout/stderr
        # T041: Pass env parameter to enable research mode in script
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(mock_script),  # AICODE-TODO: Replace with real script
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=subprocess_env,  # T041: Pass environment with research flag
        )

        logger.info(f"Spawned process {process.pid} for request {request_id}")

        # AICODE-NOTE: T016 - Track process for automatic cleanup on disconnect
        async with process_manager.track_process(request_id, process):

            # AICODE-NOTE: T073 - Wrap streaming in timeout to prevent runaway processes
            try:
                # AICODE-NOTE: T019 - Stream stdout line-by-line as SSE messages
                # T020 - Check disconnect on every iteration
                async with asyncio.timeout(GENERATION_TIMEOUT):
                    while not await request.is_disconnected():
                        # AICODE-NOTE: Read one line from subprocess stdout
                        line = await process.stdout.readline()

                        # AICODE-NOTE: Break if process ended (empty line indicates EOF)
                        if not line:
                            break

                        # AICODE-NOTE: Decode and strip whitespace
                        decoded_line = line.decode('utf-8').strip()

                        # AICODE-NOTE: T080 - Send as JSON formatted SSE message (FR-042)
                        # Frontend expects: data: {"type":"log","message":"..."}\n\n
                        log_message = {
                            "type": "log",
                            "message": decoded_line
                        }
                        yield f"data: {json.dumps(log_message)}\n\n"

                        logger.debug(f"Streamed line: {decoded_line}")

                    # AICODE-NOTE: Wait for process to complete
                    return_code = await process.wait()

            except asyncio.TimeoutError:
                # AICODE-NOTE: T073 - Handle timeout by terminating process
                logger.warning(f"Generation timeout after {GENERATION_TIMEOUT}s for request {request_id}")

                # AICODE-NOTE: T080 - Send error as JSON formatted message (FR-042)
                # Process cleanup handled by context manager
                error_message = {
                    "type": "error",
                    "message": f"Generation exceeded timeout ({GENERATION_TIMEOUT // 60} minutes)",
                    "error_type": "timeout"
                }
                yield f"data: {json.dumps(error_message)}\n\n"

                close_message = {"type": "close", "message": "done"}
                yield f"data: {json.dumps(close_message)}\n\n"
                return

            # AICODE-NOTE: T020 - Check if client disconnected during streaming
            if await request.is_disconnected():
                logger.warning(f"Client disconnected for request {request_id}")
                # AICODE-NOTE: Cleanup handled by context manager
                return

            # AICODE-NOTE: Handle process exit status
            if return_code != 0:
                # AICODE-NOTE: T047 - Send structured error event for non-zero exit (FR-020)
                stderr = await process.stderr.read()
                error_msg = stderr.decode('utf-8').strip() if stderr else "Unknown error"
                logger.error(f"Process failed with code {return_code}: {error_msg}")

                # AICODE-NOTE: T080 - Send error as JSON formatted message (FR-042)
                # Format: data: {"type":"error","message":"...","error_type":"..."}\n\n
                error_message = {
                    "type": "error",
                    "message": f"Script failed with exit code {return_code}",
                    "error_type": "process",
                    "details": error_msg if error_msg else None
                }
                yield f"data: {json.dumps(error_message)}\n\n"
            else:
                # AICODE-NOTE: T030 - Success: read output.txt and send result event
                logger.success(f"Generation completed for request {request_id}")

                # AICODE-NOTE: T030 - Read article content from output.txt (FR-019)
                # Script should write final article to output.txt in working directory
                output_file = Path("output.txt")

                # AICODE-NOTE: T075 - Maximum article length validation (50,000 chars, SC-008)
                MAX_ARTICLE_LENGTH = 50000

                if output_file.exists():
                    try:
                        article_content = output_file.read_text(encoding="utf-8")
                        logger.info(f"Read {len(article_content)} chars from output.txt")

                        # AICODE-NOTE: T075 - Validate article length doesn't exceed limit
                        if len(article_content) > MAX_ARTICLE_LENGTH:
                            logger.warning(
                                f"Article length {len(article_content)} exceeds limit {MAX_ARTICLE_LENGTH}"
                            )
                            # Truncate with warning message
                            truncated_content = article_content[:MAX_ARTICLE_LENGTH]
                            truncated_content += (
                                f"\n\n[Article truncated: exceeded {MAX_ARTICLE_LENGTH} character limit. "
                                f"Original length: {len(article_content)} characters]"
                            )
                            # AICODE-NOTE: T080 - Send result as JSON formatted message (FR-042)
                            result_message = {"type": "result", "message": truncated_content}
                            yield f"data: {json.dumps(result_message)}\n\n"
                        else:
                            # AICODE-NOTE: T080 - Send result as JSON formatted message (FR-042)
                            result_message = {"type": "result", "message": article_content}
                            yield f"data: {json.dumps(result_message)}\n\n"
                    except Exception as e:
                        # AICODE-NOTE: Handle file read errors gracefully
                        logger.error(f"Failed to read output.txt: {e}")
                        # AICODE-NOTE: T080 - Send error as JSON formatted message (FR-042)
                        error_message = {
                            "type": "error",
                            "message": f"Failed to read generated article: {str(e)}",
                            "error_type": "file_read"
                        }
                        yield f"data: {json.dumps(error_message)}\n\n"
                else:
                    # AICODE-NOTE: Fallback if output.txt doesn't exist
                    logger.warning("output.txt not found, using fallback message")
                    # AICODE-NOTE: T080 - Send result as JSON formatted message (FR-042)
                    result_message = {
                        "type": "result",
                        "message": "Article generated successfully (output.txt not found)"
                    }
                    yield f"data: {json.dumps(result_message)}\n\n"

            # AICODE-NOTE: T080 - Send close as JSON formatted message (FR-042)
            close_message = {"type": "close", "message": "done"}
            yield f"data: {json.dumps(close_message)}\n\n"

    except Exception as e:
        # AICODE-NOTE: T047 - Handle unexpected errors with structured error event
        logger.exception(f"Error during generation for request {request_id}")

        # AICODE-NOTE: T080 - Send error as JSON formatted message (FR-042)
        error_message = {
            "type": "error",
            "message": "Unexpected error during generation",
            "error_type": "unknown",
            "details": str(e)
        }
        yield f"data: {json.dumps(error_message)}\n\n"

        close_message = {"type": "close", "message": "done"}
        yield f"data: {json.dumps(close_message)}\n\n"


def validate_request_params(
    topic: str = Query(
        ...,
        min_length=1,
        max_length=1000,
        description="Article topic (1-1000 characters)"
    ),
    urls: str = Query(
        ...,
        description="Source URLs (newline or comma separated, 1-10 URLs)"
    ),
    research: bool = Query(
        False,
        description="Enable research mode"
    )
) -> GenerateArticleRequest:
    """
    Validate and parse request parameters.

    AICODE-NOTE: T032 - Request validation dependency (FR-032).
    Validates topic (1-1000 chars) and URLs (1-10 valid HTTP/HTTPS).
    FastAPI will catch ValidationError and return 422 automatically.

    Args:
        topic: Article topic
        urls: Source URLs string
        research: Research flag

    Returns:
        Validated GenerateArticleRequest

    Raises:
        HTTPException: 422 if validation fails (handled by FastAPI)
    """
    # AICODE-NOTE: Pydantic validation happens here
    # If validation fails, FastAPI converts ValidationError to 422 response
    try:
        return GenerateArticleRequest(
            topic=topic,
            source_urls=urls,
            research=research
        )
    except ValidationError as e:
        # AICODE-NOTE: Raise HTTPException with JSON-serializable error details
        # This must be raised before the endpoint starts streaming
        # Convert Pydantic errors to JSON-safe format
        errors = []
        for error in e.errors():
            # AICODE-NOTE: Remove 'ctx' field which may contain non-serializable objects
            safe_error = {k: v for k, v in error.items() if k != 'ctx'}
            # AICODE-NOTE: Add error message and location
            safe_error['message'] = error['msg']
            errors.append(safe_error)

        logger.warning(f"Validation failed: {errors}")
        raise HTTPException(status_code=422, detail=errors) from e


@router.get("/generate")
async def stream_generation(
    request: Request,
    params: GenerateArticleRequest = Depends(validate_request_params)
) -> StreamingResponse:
    """
    SSE endpoint for real-time article generation streaming.

    AICODE-NOTE: T017 - FastAPI router endpoint with SSE streaming response.
    AICODE-NOTE: T032 - Input validation via dependency (FR-032).

    Args:
        request: FastAPI request object
        params: Validated request parameters (injected via Depends)

    Returns:
        StreamingResponse with SSE stream
    """
    logger.info(
        f"Received generation request: topic={params.topic}, "
        f"research={params.research}"
    )

    # AICODE-NOTE: Return StreamingResponse with SSE media type
    return StreamingResponse(
        generate_article_stream(
            request,
            params.topic,
            params.source_urls,
            params.research
        ),
        media_type="text/event-stream",
        headers={
            # AICODE-NOTE: Required headers for SSE
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # AICODE-NOTE: Allow CORS for frontend (adjust in production)
            "Access-Control-Allow-Origin": "*",
        }
    )
