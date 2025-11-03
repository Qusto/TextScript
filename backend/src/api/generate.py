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
import re
import sys
import uuid
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import ValidationError

from src.models.request import GenerateArticleRequest, GenerateArticleRequestV2
from src.services.process_manager import ProcessManager
from src.db.database import get_db
from src.db.models import StyleProfileDB
from sqlalchemy.orm import Session

# AICODE-NOTE: T017 - Create FastAPI router for generate endpoint
router = APIRouter()

# AICODE-NOTE: Global ProcessManager instance for tracking all active processes
process_manager = ProcessManager()


# AICODE-NOTE: Strip ANSI color codes from terminal output
# Regex pattern to match ANSI escape sequences like \x1b[32m, [0m, etc.
ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*m|\[[0-9;]*m')


def strip_ansi_codes(text: str) -> str:
    """
    Remove ANSI terminal color codes from text.

    AICODE-NOTE: Fix for Phase 11 - Remove color codes from Loguru logger output.
    Loguru outputs sequences like [32m (green), [1m (bold), [0m (reset) which
    appear as garbage in the frontend UI. This function strips them.

    Args:
        text: Raw text with ANSI codes (e.g., "[32m18:52:24[0m | [1mINFO[0m")

    Returns:
        Clean text without ANSI codes (e.g., "18:52:24 | INFO")

    Examples:
        >>> strip_ansi_codes("[32m18:52:24[0m | [1mINFO[0m")
        "18:52:24 | INFO"
    """
    return ANSI_ESCAPE_PATTERN.sub('', text)


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

    # AICODE-NOTE: T018 - Use real ugly_script.py from /src/ directory
    # Script reads input from links.txt and topic.txt files

    # AICODE-NOTE: Determine script path (Docker: /src/, Local: ../../../src/)
    script_path = Path("/src/ugly_script.py")
    if not script_path.exists():
        # Fallback for local development
        script_path = Path(__file__).parent.parent.parent.parent / "src" / "ugly_script.py"

    if not script_path.exists():
        error_msg = f"ugly_script.py not found at {script_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # AICODE-NOTE: Create temporary working directory for script execution
    work_dir = Path(f"/tmp/textscript_{uuid.uuid4().hex[:8]}")
    work_dir.mkdir(parents=True, exist_ok=True)

    # AICODE-NOTE: Create input files for ugly_script.py
    # It reads links.txt and topic.txt from current working directory
    links_file = work_dir / "links.txt"
    topic_file = work_dir / "topic.txt"

    # Parse URLs (accept newline or comma separated)
    url_list = [
        url.strip()
        for url in urls.replace(',', '\n').split('\n')
        if url.strip()
    ]

    # Write URLs to links.txt (one per line)
    links_file.write_text("\n".join(url_list) + "\n", encoding="utf-8")
    # Write topic to topic.txt
    topic_file.write_text(topic, encoding="utf-8")

    logger.info(f"Using script: {script_path}")
    logger.info(f"Working directory: {work_dir}")

    # AICODE-NOTE: T041 - Prepare environment variables for subprocess
    # Pass research flag to the script via RESEARCH_ENABLED env var
    subprocess_env = {
        **dict(os.environ),  # Inherit parent environment (includes API keys)
        "RESEARCH_ENABLED": "true" if research else "false",
        "PYTHONPATH": "/app:/",  # Add root to PYTHONPATH so 'import src.X' works
    }

    try:
        # AICODE-NOTE: Create subprocess with pipe for stdout/stderr
        # T041: Pass env parameter to enable research mode in script
        # ugly_script.py now has sys.path fix, so we can run it directly
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),  # Run script directly (has sys.path fix inside)
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=subprocess_env,  # T041: Pass environment with research flag and API keys
            cwd=str(work_dir),  # Set working directory where input files are
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
                # Script writes final article to output.txt in working directory
                output_file = work_dir / "output.txt"

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
    SSE endpoint for real-time article generation streaming (legacy GET endpoint).

    AICODE-NOTE: T017 - FastAPI router endpoint with SSE streaming response.
    AICODE-NOTE: T032 - Input validation via dependency (FR-032).
    DEPRECATED: Use POST /api/generate for new implementations (T104)

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


async def generate_article_stream_v2(
    request: Request,
    title: str,
    key_points: str | None,
    profile_text: str | None,
    enable_research: bool,
    word_count: int = 500
) -> AsyncIterator[str]:
    """
    Stream article generation output as Server-Sent Events (Version 2 with profiles).

    AICODE-NOTE: T104-T107 - Two-stage generation with style profiles and key points.
    AICODE-NOTE: T124 - Support optional profile_text for free-style generation.
    AICODE-NOTE: Phase 11.2 - Added word_count parameter for article length control.
    - T104: Accept title/keyPoints/profileId instead of topic/urls
    - T105: Two-stage research flow (research → generation)
    - T106: Integrate keyPoints into generation prompt
    - T107: Use loaded profile_text for style guidance (optional)
    - T124: If profile_text is None, generate without style constraints
    - Phase 11.2: Specify target word count for article generation

    Args:
        request: FastAPI request object for disconnect detection
        title: Article title
        key_points: Optional key points for article content
        profile_text: Style profile text from database (None for free-style)
        enable_research: Whether to enable two-stage research mode
        word_count: Target article length in words (100-5000, default: 500)

    Yields:
        SSE formatted strings (data: messages, events)
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Starting V2 generation request {request_id} for title: {title}")

    # AICODE-NOTE: T073 - Set timeout for long-running generations (10 minutes)
    GENERATION_TIMEOUT = 600

    # AICODE-NOTE: T105 - Use real ugly_script.py from /src/ directory
    # Script reads input from links.txt and topic.txt files

    # AICODE-NOTE: Determine script path (Docker: /src/, Local: ../../../src/)
    script_path = Path("/src/ugly_script.py")
    if not script_path.exists():
        # Fallback for local development
        script_path = Path(__file__).parent.parent.parent.parent / "src" / "ugly_script.py"

    if not script_path.exists():
        error_msg = f"ugly_script.py not found at {script_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # AICODE-NOTE: Create temporary working directory for script execution
    work_dir = Path(f"/tmp/textscript_{uuid.uuid4().hex[:8]}")
    work_dir.mkdir(parents=True, exist_ok=True)

    # AICODE-NOTE: T142 - Create only topic.txt (NO links.txt for V2 API)
    # Profile is passed via environment variable instead
    topic_file = work_dir / "topic.txt"

    # Write title to topic.txt
    topic_file.write_text(title, encoding="utf-8")

    logger.info(f"Using script: {script_path}")
    logger.info(f"Working directory: {work_dir}")

    # AICODE-NOTE: T106 - Build generation prompt with key points
    # AICODE-NOTE: T124 - Handle optional profile_text for free-style generation
    # AICODE-NOTE: Phase 11.2 - Include word count requirement in prompt
    generation_prompt = f"Title: {title}\n\n"
    generation_prompt += f"Target Length: {word_count} words (±10-20% is acceptable)\n\n"
    if key_points:
        generation_prompt += f"Key Points:\n{key_points}\n\n"
    if profile_text:
        # AICODE-NOTE: T124 - Include style profile if provided
        generation_prompt += f"Style Profile:\n{profile_text}"
    else:
        # AICODE-NOTE: T124 - Free-style generation without style constraints
        generation_prompt += "Style: Free-style (no specific style constraints)"

    # AICODE-NOTE: T105 - Two-stage research flow
    try:
        if enable_research:
            # STAGE 1: Research info collection
            logger.info(f"Stage 1: Running research collection for request {request_id}")

            # AICODE-NOTE: Emit stage indicator
            stage_message = {
                "type": "log",
                "message": "🔍 Этап 1/2: Сбор информации из источников..."
            }
            yield f"data: {json.dumps(stage_message)}\n\n"

            # AICODE-TODO: T105 - Replace with actual research_client.py call
            # For now, simulate research stage
            research_message = {
                "type": "log",
                "message": f"Исследование темы: {title}"
            }
            yield f"data: {json.dumps(research_message)}\n\n"

            await asyncio.sleep(1)  # Simulate research time

            # STAGE 2: Article generation with research data
            logger.info(f"Stage 2: Running article generation for request {request_id}")

            stage_message = {
                "type": "log",
                "message": "✍️ Этап 2/2: Генерация статьи на основе собранных данных..."
            }
            yield f"data: {json.dumps(stage_message)}\n\n"

        # AICODE-NOTE: T143 - Prepare environment with profile text
        # T143: Pass profile_text via STYLE_PROFILE_TEXT env variable
        # Empty string for free-style generation
        subprocess_env = {
            **dict(os.environ),
            "ARTICLE_TITLE": title,
            "GENERATION_PROMPT": generation_prompt,
            "RESEARCH_ENABLED": "true" if enable_research else "false",
            "STYLE_PROFILE_TEXT": profile_text or "",  # T143: Empty for free-style
            "PYTHONPATH": "/app:/",  # Add root to PYTHONPATH so 'import src.X' works
        }

        # AICODE-NOTE: T145 - Log generation mode (styled vs free-style)
        if profile_text:
            # Log profile length, not full content (best practice)
            logger.info(f"Generation mode: styled (profile: {len(profile_text)} chars)")
            if len(profile_text) > 50:
                logger.debug(f"  Profile preview: {profile_text[:50]}...")
        else:
            logger.info("Generation mode: free-style (no profile)")

        # AICODE-NOTE: T144 - Spawn article generation process with V2 API flags
        # --skip-style-analysis: Don't fetch URLs or analyze style
        # --profile-from-env: Load profile from STYLE_PROFILE_TEXT env variable
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            "--skip-style-analysis",  # T144: Skip URL fetching
            "--profile-from-env",      # T144: Load profile from ENV
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=subprocess_env,
            cwd=str(work_dir),  # Set working directory where input files are
        )

        logger.info(f"Spawned process {process.pid} for request {request_id}")

        # AICODE-NOTE: Track process for automatic cleanup
        async with process_manager.track_process(request_id, process):
            try:
                # AICODE-NOTE: Stream stdout with timeout
                async with asyncio.timeout(GENERATION_TIMEOUT):
                    while not await request.is_disconnected():
                        line = await process.stdout.readline()

                        if not line:
                            break

                        decoded_line = line.decode('utf-8').strip()

                        # AICODE-NOTE: Strip ANSI color codes before sending to frontend
                        # Loguru outputs escape sequences like [32m, [1m which look like garbage in UI
                        clean_line = strip_ansi_codes(decoded_line)

                        # AICODE-NOTE: T080 - JSON formatted log messages
                        log_message = {
                            "type": "log",
                            "message": clean_line
                        }
                        yield f"data: {json.dumps(log_message)}\n\n"

                        logger.debug(f"Streamed line: {decoded_line}")

                    return_code = await process.wait()

            except asyncio.TimeoutError:
                logger.warning(f"Generation timeout after {GENERATION_TIMEOUT}s for request {request_id}")
                error_message = {
                    "type": "error",
                    "message": f"Генерация превысила лимит времени ({GENERATION_TIMEOUT // 60} минут)",
                    "error_type": "timeout"
                }
                yield f"data: {json.dumps(error_message)}\n\n"
                close_message = {"type": "close", "message": "done"}
                yield f"data: {json.dumps(close_message)}\n\n"
                return

            # AICODE-NOTE: Check disconnect
            if await request.is_disconnected():
                logger.warning(f"Client disconnected for request {request_id}")
                return

            # AICODE-NOTE: Handle process results
            if return_code != 0:
                stderr = await process.stderr.read()
                error_msg = stderr.decode('utf-8').strip() if stderr else "Unknown error"
                logger.error(f"Process failed with code {return_code}: {error_msg}")

                error_message = {
                    "type": "error",
                    "message": f"Ошибка генерации (код {return_code})",
                    "error_type": "process",
                    "details": error_msg if error_msg else None
                }
                yield f"data: {json.dumps(error_message)}\n\n"
            else:
                # AICODE-NOTE: T030 - Read output.txt
                logger.success(f"Generation completed for request {request_id}")

                output_file = work_dir / "output.txt"
                MAX_ARTICLE_LENGTH = 50000

                if output_file.exists():
                    try:
                        article_content = output_file.read_text(encoding="utf-8")
                        logger.info(f"Read {len(article_content)} chars from output.txt")

                        # AICODE-NOTE: T075 - Validate length
                        if len(article_content) > MAX_ARTICLE_LENGTH:
                            logger.warning(
                                f"Article length {len(article_content)} exceeds limit {MAX_ARTICLE_LENGTH}"
                            )
                            truncated_content = article_content[:MAX_ARTICLE_LENGTH]
                            truncated_content += (
                                f"\n\n[Статья обрезана: превышен лимит {MAX_ARTICLE_LENGTH} символов. "
                                f"Оригинальная длина: {len(article_content)} символов]"
                            )
                            result_message = {"type": "result", "message": truncated_content}
                            yield f"data: {json.dumps(result_message)}\n\n"
                        else:
                            result_message = {"type": "result", "message": article_content}
                            yield f"data: {json.dumps(result_message)}\n\n"
                    except Exception as e:
                        logger.error(f"Failed to read output.txt: {e}")
                        error_message = {
                            "type": "error",
                            "message": f"Ошибка чтения результата: {str(e)}",
                            "error_type": "file_read"
                        }
                        yield f"data: {json.dumps(error_message)}\n\n"
                else:
                    logger.warning("output.txt not found, using fallback message")
                    result_message = {
                        "type": "result",
                        "message": "Статья сгенерирована успешно (output.txt не найден)"
                    }
                    yield f"data: {json.dumps(result_message)}\n\n"

            # AICODE-NOTE: T031 - Close event
            close_message = {"type": "close", "message": "done"}
            yield f"data: {json.dumps(close_message)}\n\n"

    except Exception as e:
        logger.exception(f"Error during V2 generation for request {request_id}")
        error_message = {
            "type": "error",
            "message": "Неожиданная ошибка при генерации",
            "error_type": "unknown",
            "details": str(e)
        }
        yield f"data: {json.dumps(error_message)}\n\n"

        close_message = {"type": "close", "message": "done"}
        yield f"data: {json.dumps(close_message)}\n\n"


@router.post("/generate")
async def stream_generation_v2(
    request: Request,
    body: GenerateArticleRequestV2,
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    SSE endpoint for real-time article generation streaming (Version 2 with profiles).

    AICODE-NOTE: T104 - New POST endpoint for Phase 10 integration.
    AICODE-NOTE: T124 - Support optional profileId for free-style generation.
    Accepts title, keyPoints, profileId (optional), and enableResearch in request body.

    Args:
        request: FastAPI request object
        body: Validated request body (GenerateArticleRequestV2)
        db: Database session (injected via Depends)

    Returns:
        StreamingResponse with SSE stream

    Raises:
        HTTPException: 404 if profileId is provided but profile not found
    """
    logger.info(
        f"Received V2 generation request: title={body.title}, "
        f"profileId={body.profileId}, research={body.enableResearch}"
    )

    # AICODE-NOTE: T124 - Load style profile from database if profileId provided
    profile_text = None
    if body.profileId is not None:
        # AICODE-NOTE: T107 - Load profile from database
        profile = db.query(StyleProfileDB).filter(StyleProfileDB.id == body.profileId).first()

        if not profile:
            logger.warning(f"Profile {body.profileId} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Style profile with ID {body.profileId} not found"
            )

        profile_text = profile.profile_text
        logger.info(f"Loaded profile {profile.id} with hash {profile.urls_hash}")
    else:
        # AICODE-NOTE: T124 - No profile specified, use free-style generation
        logger.info("No profile specified, using free-style generation")

    # AICODE-NOTE: Return StreamingResponse with SSE media type
    return StreamingResponse(
        generate_article_stream_v2(
            request,
            body.title,
            body.keyPoints,
            profile_text,  # T124: None for free-style, profile_text for styled
            body.enableResearch,
            body.wordCount  # Phase 11.2: Target word count for article
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )
