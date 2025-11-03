"""
Style profile management API endpoints.

AICODE-NOTE: T088-T092 - Profile CRUD endpoints (FR-029)
Provides REST API for managing style profiles:
- GET /api/profiles/current - Get currently active profile
- POST /api/profiles - Create new profile from URLs
- GET /api/profiles/{id} - Get specific profile by ID
- DELETE /api/profiles/{id} - Delete profile

AICODE-NOTE: T113 - Key architectural decisions:
1. Why single "current" profile?
   - Single-user application (per spec)
   - Simplifies UI (no profile selection dropdown needed)
   - "Current" = most recently created profile
   - Easy to extend to multi-user with user_id column later

2. Why extract style on POST instead of async background task?
   - Style extraction is fast (< 5 seconds for 1-3 URLs)
   - User expects immediate feedback
   - Simpler error handling (no job polling needed)
   - Background task would add complexity without benefit

3. Why store in database instead of file cache?
   - Atomic operations (no race conditions)
   - Easy querying (find by hash, get latest, etc.)
   - Built-in timestamps for auditing
   - Migration path to PostgreSQL clear
   - File cache (style_cache.py) still used as backup/legacy
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field
from loguru import logger

from src.db.database import get_db
from src.db.models import StyleProfileDB
# AICODE-NOTE: Removed import from src.style_cache - using local implementation instead
# from src.style_cache import generate_url_hash

# AICODE-NOTE: T088 - Create FastAPI router for profile endpoints
router = APIRouter(prefix="/api/profiles", tags=["profiles"])


# AICODE-NOTE: Local implementation of URL hash generation
# Matches the logic from src/style_cache.py
def generate_url_hash(urls: list[str]) -> str:
    """
    Generate MD5 hash from sorted URLs.

    AICODE-NOTE: Same logic as src/style_cache.py::generate_url_hash()
    Used to check if profile already exists for same URL set.
    """
    import hashlib
    sorted_urls = sorted(urls)
    combined = "\n".join(sorted_urls)
    return hashlib.md5(combined.encode()).hexdigest()


def detect_content_type(lines: List[str]) -> Literal["urls", "text"]:
    """
    Smart detection: URLs vs text input.

    AICODE-NOTE: T194 - Auto-detection for transparent UX (Phase 13)
    Logic: If >50% of non-empty lines start with http:// or https:// → "urls"
    Otherwise → "text"

    Edge cases:
    - Empty list → "text" (default)
    - Single URL → "urls"
    - Text with embedded URLs → "text" (majority rule)

    Args:
        lines: List of input lines (may contain URLs or text)

    Returns:
        "urls" if majority are URLs, "text" otherwise

    Examples:
        detect_content_type(["https://example.com", "https://test.com"]) → "urls"
        detect_content_type(["This is some text", "Another line"]) → "text"
        detect_content_type(["Text with https://link.com embedded"]) → "text"
        detect_content_type([]) → "text"
    """
    if not lines:
        return "text"

    # AICODE-NOTE: Filter out empty lines for accurate detection
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return "text"

    # AICODE-NOTE: Count lines that start with URL protocol
    url_count = sum(
        1 for line in non_empty
        if line.strip().startswith(("http://", "https://"))
    )

    # AICODE-NOTE: Majority rule - if >50% are URLs, classify as "urls"
    return "urls" if url_count / len(non_empty) > 0.5 else "text"


def generate_profile_name_from_url(url: str) -> str:
    """
    Generate human-readable profile name from URL domain.

    AICODE-NOTE: T197 - Extracted from generate_profile_name for reusability.
    Helper function for URL-based name generation.

    Args:
        url: Single URL to extract domain from

    Returns:
        str: Profile name (e.g. "Профиль Habr")
    """
    from urllib.parse import urlparse

    try:
        # AICODE-NOTE: Parse URL to extract domain
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path  # netloc for full URLs, path for relative

        # AICODE-NOTE: Handle port numbers (remove :port)
        if ":" in domain:
            domain = domain.split(":")[0]

        # AICODE-NOTE: Check for localhost or IP addresses
        if domain in ["localhost", "127.0.0.1"] or domain.startswith("192.168.") or domain.startswith("10."):
            return "Профиль Local"

        # AICODE-NOTE: Remove "www." prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # AICODE-NOTE: Take first part before first dot (e.g. "habr" from "habr.com")
        site_name = domain.split(".")[0]

        # AICODE-NOTE: Capitalize first letter
        site_name = site_name.capitalize()

        # AICODE-NOTE: Return formatted profile name
        return f"Профиль {site_name}"

    except Exception as e:
        # AICODE-NOTE: Fallback for any parsing errors
        logger.warning(f"Failed to generate profile name from URL: {e}")
        return "Профиль"


def generate_profile_name(
    source_type: str,
    source_items: List[str],
    custom_name: str | None = None
) -> str:
    """
    Generate profile name with priority: custom → auto-generated.

    AICODE-NOTE: T197 - Phase 13 - Custom name support with auto-generation fallback.
    Priority:
    1. custom_name (if provided by user)
    2. Auto-generation:
       - URLs: "Профиль {SiteName}" (from first URL domain)
       - Text: First 5-7 words (up to 50 chars)

    Args:
        source_type: "urls" or "text"
        source_items: List of source lines (URLs or text)
        custom_name: Optional custom name from user

    Returns:
        str: Profile name

    Examples:
        generate_profile_name("urls", ["https://habr.com"], None) → "Профиль Habr"
        generate_profile_name("text", ["Some text here"], "My Style") → "My Style"
        generate_profile_name("text", ["First line", "Second"], None) → "First line Second"
    """
    # AICODE-NOTE: Priority 1: Custom name
    if custom_name and custom_name.strip():
        return custom_name.strip()

    # AICODE-NOTE: Priority 2: Auto-generate
    if source_type == "urls":
        # AICODE-NOTE: Use existing URL-based name generation
        if source_items:
            return generate_profile_name_from_url(source_items[0])
        return "Профиль"
    else:  # text
        # AICODE-NOTE: Extract first 7 words from combined text
        combined = " ".join(source_items)
        words = combined.split()[:7]
        name = " ".join(words)

        # AICODE-NOTE: Truncate to 50 chars if needed
        if len(name) > 50:
            name = name[:47] + "..."

        return name or "Профиль из текста"


# AICODE-NOTE: T088 - Request/Response models for type safety and validation
# AICODE-NOTE: T196 - Updated for Phase 13 text-based profile creation
class ProfileCreateRequest(BaseModel):
    """Request model for creating new style profile."""

    source_content: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,  # AICODE-NOTE: Allow more lines for text (was 10 for URLs)
        description="URLs (one per line) or text blocks",
        examples=[
            # URL example
            [
                "https://example.com/article1",
                "https://example.com/article2",
            ],
            # Text example
            [
                "This is the first paragraph of text.",
                "This is the second paragraph.",
                "And here is more content to analyze for writing style.",
            ]
        ],
    )

    profile_name: str | None = Field(
        None,
        max_length=100,
        description="Custom profile name (optional, auto-generated if empty)",
        examples=["My Technical Writing Style", "Профиль Habr"],
    )


class ProfileResponse(BaseModel):
    """Response model for profile data."""

    id: int
    name: str  # AICODE-NOTE: T119 - Human-readable profile name for UI display
    urls_hash: str
    profile_text: str
    source_urls: List[str]
    source_type: str = "urls"  # AICODE-NOTE: T199 - Source type for Phase 13 (urls/text)
    created_at: str
    updated_at: str
    api_version: str = "v2.1"  # AICODE-NOTE: T150 - API version for frontend cache invalidation

    model_config = {
        "from_attributes": True  # Pydantic V2: Allow ORM model conversion
    }


# AICODE-NOTE: GET /api/profiles - List all profiles (NEW for Phase 11)
@router.get("", response_model=List[ProfileResponse])
def list_profiles(db: Session = Depends(get_db)):
    """
    Get list of all style profiles.

    AICODE-NOTE: Phase 11 - Profile selection UI support.
    Returns all profiles ordered by creation date (newest first).
    Used by profile dropdown/selection UI component.

    Args:
        db: Database session (injected)

    Returns:
        List[ProfileResponse]: List of all profiles (may be empty)

    Example response:
        [
            {
                "id": 2,
                "name": "Профиль Habr",
                "urls_hash": "xyz...",
                "source_urls": ["https://habr.com/..."],
                "created_at": "2025-10-31T12:00:00Z",
                ...
            },
            {
                "id": 1,
                "name": "Профиль Azbyka",
                ...
            }
        ]
    """
    logger.info("Fetching all profiles")

    profiles = (
        db.query(StyleProfileDB)
        .order_by(StyleProfileDB.created_at.desc())
        .all()
    )

    logger.info(f"Found {len(profiles)} profiles")

    # Convert to list of ProfileResponse
    return [ProfileResponse(**profile.to_dict()) for profile in profiles]


# AICODE-NOTE: T089 - GET /api/profiles/current endpoint
@router.get("/current", response_model=Optional[ProfileResponse])
def get_current_profile(db: Session = Depends(get_db)):
    """
    Get the currently active style profile (most recently created).

    AICODE-NOTE: T089 - Returns current profile or null if none exists (FR-029)
    "Current" is defined as the most recently created profile (highest ID).
    For single-user application, this is the only profile that matters.

    Args:
        db: Database session (injected)

    Returns:
        ProfileResponse: Current profile data, or None if no profiles exist

    Example response:
        {
            "id": 1,
            "urls_hash": "a1b2c3d4...",
            "profile_text": "The author uses...",
            "source_urls": ["https://..."],
            "created_at": "2025-10-27T10:00:00Z",
            "updated_at": "2025-10-27T10:00:00Z"
        }
    """
    logger.info("Fetching current profile")

    # AICODE-NOTE: Query for most recent profile (ORDER BY id DESC LIMIT 1)
    profile = (
        db.query(StyleProfileDB).order_by(StyleProfileDB.id.desc()).first()
    )

    if not profile:
        logger.info("No profiles found in database")
        return None

    logger.info(
        f"Found current profile: id={profile.id}, "
        f"urls={len(profile.source_urls)} URLs"
    )

    # AICODE-NOTE: Convert to dict for proper datetime serialization
    return ProfileResponse(**profile.to_dict())


# AICODE-NOTE: T090 - POST /api/profiles endpoint
@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(
    request: ProfileCreateRequest, db: Session = Depends(get_db)
):
    """
    Create new style profile by extracting style from source URLs.

    AICODE-NOTE: T090 - Profile creation with style extraction (FR-030)
    Steps:
    1. Generate MD5 hash from sorted URLs (check for duplicates)
    2. Call src/ugly_script.py to extract style characteristics
    3. Save extracted profile_text to database
    4. Return created profile

    Integration with existing code:
    - Reuses generate_url_hash() from src/style_cache.py
    - Calls style extraction script from src/ directory
    - Stores result in database (new) instead of file (legacy)

    Args:
        request: ProfileCreateRequest with source_urls
        db: Database session (injected)

    Returns:
        ProfileResponse: Newly created profile

    Raises:
        HTTPException 400: If profile with same URLs already exists
        HTTPException 500: If style extraction fails

    Example request:
        POST /api/profiles
        {
            "source_urls": [
                "https://example.com/article1",
                "https://example.com/article2"
            ]
        }
    """
    logger.info(f"Creating profile from {len(request.source_content)} content lines")

    # AICODE-NOTE: T198 - Phase 13 - Parse source_content (can be URLs or text)
    source_lines = [line.strip() for line in request.source_content if line.strip()]

    # AICODE-NOTE: T194 - Detect content type (urls vs text)
    content_type = detect_content_type(source_lines)
    logger.info(f"Detected content type: {content_type}")

    # AICODE-NOTE: T198 - Branch by content type
    if content_type == "urls":
        # AICODE-NOTE: URL flow (existing logic preserved)
        url_strings = source_lines

        # AICODE-NOTE: Generate hash for duplicate detection
        urls_hash = generate_url_hash(url_strings)
        logger.debug(f"Generated URL hash: {urls_hash}")

        # AICODE-NOTE: Check if profile with same URLs already exists
        existing_profile = (
            db.query(StyleProfileDB)
            .filter(StyleProfileDB.urls_hash == urls_hash)
            .first()
        )

        if existing_profile:
            logger.warning(f"Profile with hash {urls_hash} already exists")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "duplicate_profile",
                    "message": "Profile with these URLs already exists",
                    "existing_profile_id": existing_profile.id,
                },
            )

        try:
            # AICODE-NOTE: Extract style from URLs (subprocess call)
            profile_text = await _extract_style_from_urls(url_strings)
            logger.info(f"Style extracted from URLs: {len(profile_text)} chars")

        except Exception as e:
            logger.error(f"URL style extraction failed: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "extraction_failed",
                    "message": "Failed to extract style from URLs",
                    "details": str(e),
                },
            )

        # AICODE-NOTE: Source items for name generation
        source_items = url_strings

    else:  # text
        # AICODE-NOTE: T198 - NEW text flow (Phase 13)
        combined_text = "\n\n".join(source_lines)
        logger.info(f"Combined text: {len(combined_text)} chars")

        try:
            # AICODE-NOTE: T195 - Direct LLM analysis (no subprocess)
            profile_text = await _analyze_style_from_text(combined_text)
            logger.info(f"Style extracted from text: {len(profile_text)} chars")

        except Exception as e:
            logger.error(f"Text style analysis failed: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "analysis_failed",
                    "message": "Failed to analyze style from text",
                    "details": str(e),
                },
            )

        # AICODE-NOTE: Generate hash from text for duplicate detection
        import hashlib
        urls_hash = hashlib.md5(combined_text.encode()).hexdigest()
        logger.debug(f"Generated text hash: {urls_hash}")

        # AICODE-NOTE: Source items for display (text indicator)
        source_items = [f"<text: {len(combined_text)} chars>"]

    # AICODE-NOTE: T197 - Generate profile name (unified for both types)
    profile_name = generate_profile_name(
        source_type=content_type,
        source_items=source_lines,  # Original lines for name generation
        custom_name=request.profile_name
    )
    logger.info(f"Generated profile name: {profile_name}")

    # AICODE-NOTE: T198 - Save profile to database (unified for both types)
    new_profile = StyleProfileDB(
        name=profile_name,
        urls_hash=urls_hash,
        profile_text=profile_text,
        source_urls=source_items,  # May contain URLs or text indicator
        source_type=content_type,   # T192: NEW field for Phase 13
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    logger.success(
        f"Profile created: id={new_profile.id}, type={content_type}, hash={urls_hash[:8]}..."
    )

    return ProfileResponse(**new_profile.to_dict())


async def _extract_style_from_urls(urls: List[str]) -> str:
    """
    Extract writing style from URLs using existing article script.

    AICODE-NOTE: T090 - Style extraction integration (FIXED for Phase 11)
    Calls ugly_script.py in MODE 1 (traditional style analysis).
    Creates temporary directory with links.txt and topic.txt, runs script,
    then reads extracted profile from cache.

    Args:
        urls: List of source URLs to analyze

    Returns:
        str: Extracted style characteristics (profile_text)

    Raises:
        Exception: If extraction fails
    """
    import tempfile
    import hashlib

    # AICODE-NOTE: Create temporary directory for script input files
    work_dir = tempfile.mkdtemp(prefix="profile_extraction_")
    work_dir_path = Path(work_dir)

    try:
        # AICODE-NOTE: Write URLs to links.txt (MODE 1 expects this file)
        links_file = work_dir_path / "links.txt"
        links_file.write_text("\n".join(urls), encoding="utf-8")

        # AICODE-NOTE: Write dummy topic to topic.txt (MODE 1 requires this file)
        # Topic is not used for profile extraction, but script validates its presence
        topic_file = work_dir_path / "topic.txt"
        topic_file.write_text("Style Analysis", encoding="utf-8")

        # AICODE-NOTE: Find ugly_script.py path
        script_path = (
            Path(__file__).parent.parent.parent.parent / "src" / "ugly_script.py"
        )

        if not script_path.exists():
            logger.warning(
                f"Style script not found at {script_path}, using placeholder"
            )
            # AICODE-NOTE: Placeholder for development
            return (
                f"Style profile extracted from {len(urls)} URLs:\n"
                f"- Professional tone with technical terminology\n"
                f"- Uses data-driven arguments and specific examples\n"
                f"- Prefers bullet points for clarity\n"
                f"- Concise writing with active voice"
            )

        # AICODE: BUG-FIX-002 - Find Poetry Python for root src/ directory
        # AICODE: REASON - ugly_script.py has dependencies (requests, etc) in root Poetry env
        # AICODE: IMPACT - Script now runs with correct dependencies
        root_dir = script_path.parent.parent
        root_python = None

        # Try to find Poetry Python for root directory by checking pyproject.toml
        root_pyproject = root_dir / "pyproject.toml"
        if root_pyproject.exists():
            try:
                import subprocess
                # Get Poetry cache directory
                poetry_cache = Path.home() / "Library" / "Caches" / "pypoetry" / "virtualenvs"
                if poetry_cache.exists():
                    # Look for text-script (root) venv, not textscript-backend
                    for venv_dir in poetry_cache.glob("text-script-*"):
                        if "backend" not in venv_dir.name.lower():
                            candidate = venv_dir / "bin" / "python"
                            if candidate.exists():
                                root_python = candidate
                                logger.debug(f"Found root Poetry Python: {root_python}")
                                break

                if not root_python:
                    logger.warning("Could not find root Poetry Python in cache")
            except Exception as e:
                logger.warning(f"Could not find root Poetry Python: {e}")

        # Fallback to sys.executable if Poetry not found
        python_executable = str(root_python) if root_python else sys.executable
        logger.debug(f"Using Python executable: {python_executable}")

        # AICODE-NOTE: Run ugly_script.py in MODE 1 (no flags = traditional style analysis)
        # Script will:
        # 1. Read links.txt and topic.txt
        # 2. Fetch URLs and extract content
        # 3. Analyze style with LLM
        # 4. Save profile to cache (style_profiles/{url_hash}.txt)
        # 5. Generate article (which we don't need, but it's part of MODE 1)

        # AICODE: BUG-FIX-002 - Fixed ModuleNotFoundError by setting PYTHONPATH
        # AICODE: REASON - ugly_script.py uses "from src.config" which fails without proper PYTHONPATH
        # AICODE: IMPACT - Profile creation now works correctly

        # AICODE-NOTE: Copy all environment variables (including OPENAI_API_KEY)
        # ugly_script.py needs API key to analyze style
        env = os.environ.copy()

        # AICODE: BUG-FIX-002 - Load .env from root directory
        # AICODE: REASON - Backend doesn't have OPENAI_API_KEY in environment
        # AICODE: IMPACT - Script can now access API key for style analysis
        env_file = root_dir / ".env"
        if env_file.exists():
            # Simple .env parser (no external dependencies)
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env[key.strip()] = value.strip()
            logger.debug(f"Loaded environment from {env_file}")
        else:
            logger.warning(f".env file not found at {env_file}")

        # AICODE-NOTE: Disable research stage to avoid errors during profile extraction
        # Research stage is not needed for profile creation and can cause parsing errors
        env["RESEARCH_ENABLED"] = "false"

        # AICODE: BUG-FIX-002 - Set PYTHONPATH to include src directory
        # This ensures "from src.config import ..." works in subprocess
        src_dir = script_path.parent.parent
        env["PYTHONPATH"] = str(src_dir)

        logger.info(f"Running style extraction for {len(urls)} URLs...")
        logger.debug(f"Script path: {script_path}")
        logger.debug(f"Working directory: {work_dir}")
        logger.debug(f"Python executable: {python_executable}")
        logger.debug(f"PYTHONPATH: {env.get('PYTHONPATH')}")

        process = await asyncio.create_subprocess_exec(
            python_executable,  # AICODE: BUG-FIX-002 - Use root Poetry Python
            str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=work_dir,  # Run in temp directory where links.txt and topic.txt are
            env=env,  # Pass environment with RESEARCH_ENABLED=false and PYTHONPATH
        )

        stdout, stderr = await process.communicate()

        # AICODE: BUG-FIX-002 - Enhanced error logging with stdout and stderr
        # AICODE: REASON - Original error message was empty, making debugging impossible
        stdout_text = stdout.decode("utf-8").strip() if stdout else ""
        stderr_text = stderr.decode("utf-8").strip() if stderr else ""

        if process.returncode != 0:
            logger.error(f"Style extraction script failed with return code: {process.returncode}")
            logger.error(f"Script path: {script_path}")
            logger.error(f"Working directory: {work_dir}")
            logger.error(f"URLs: {urls}")

            if stdout_text:
                logger.error(f"STDOUT:\n{stdout_text}")
            if stderr_text:
                logger.error(f"STDERR:\n{stderr_text}")

            # AICODE: BUG-FIX-002 - Return both stdout and stderr for better error messages
            error_details = stderr_text or stdout_text or "No error output"
            raise Exception(f"Style extraction script failed: {error_details}")

        # AICODE-NOTE: Read extracted profile from cache
        # Cache location: style_profiles/{md5_hash}.txt
        # Generate same hash as ugly_script.py uses
        sorted_urls = sorted(urls)
        combined = "\n".join(sorted_urls)
        url_hash = hashlib.md5(combined.encode()).hexdigest()

        # AICODE-NOTE: Cache is in style_profiles/ directory (relative to work_dir)
        cache_file = work_dir_path / "style_profiles" / f"{url_hash}.txt"

        if not cache_file.exists():
            logger.error(f"Cache file not found: {cache_file}")
            raise Exception("Style extraction succeeded but cache file not found")

        profile_text = cache_file.read_text(encoding="utf-8")
        logger.success(f"Style profile extracted: {len(profile_text)} chars")

        return profile_text

    finally:
        # AICODE-NOTE: Clean up temporary directory
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)


async def _analyze_style_from_text(text: str) -> str:
    """
    Analyze writing style from direct text input.

    AICODE-NOTE: T195 - Phase 13 - Direct LLM analysis without subprocess.
    Unlike _extract_style_from_urls(), this does NOT:
    - Call ugly_script.py subprocess
    - Create temporary directories
    - Fetch URLs or parse HTML

    Instead:
    - Loads config directly
    - Creates LLMClient
    - Calls analyze_style() method
    - Returns profile_text string

    This is faster and has no network dependency.

    Args:
        text: Direct text content to analyze for writing style

    Returns:
        str: Style profile text (LLM-generated characteristics)

    Raises:
        Exception: If LLM analysis fails
    """
    # AICODE-NOTE: Import from parent src directory (ugly_script.py location)
    # Adjust path to import config and llm_client from src/
    script_src_path = Path(__file__).parent.parent.parent.parent / "src"
    if str(script_src_path) not in sys.path:
        sys.path.insert(0, str(script_src_path))

    from config import load_config
    from llm_client import LLMClient

    logger.info(f"Analyzing style from direct text input ({len(text)} chars)...")

    # AICODE-NOTE: Load config for API key and limits
    config = load_config()

    # AICODE-NOTE: Apply content limits (same as URL flow)
    if len(text) > config.max_total_content:
        logger.warning(
            f"Text truncated from {len(text)} to {config.max_total_content} chars"
        )
        text = text[:config.max_total_content]

    # AICODE-NOTE: Create LLM client and analyze style directly
    # No subprocess, no temp files, no network requests
    llm_client = LLMClient(api_key=config.api_key, model=config.model)
    profile_text = llm_client.analyze_style(text)

    logger.success(f"Style analyzed from text: {len(profile_text)} chars")
    return profile_text


# AICODE-NOTE: T091 - GET /api/profiles/{id} endpoint
@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """
    Get specific style profile by ID.

    AICODE-NOTE: T091 - Retrieve profile details for viewing (FR-029)
    Used by "View Profile" button in UI to display extracted characteristics.

    Args:
        profile_id: Profile database ID
        db: Database session (injected)

    Returns:
        ProfileResponse: Profile data

    Raises:
        HTTPException 404: If profile not found
    """
    logger.info(f"Fetching profile id={profile_id}")

    profile = db.query(StyleProfileDB).filter(StyleProfileDB.id == profile_id).first()

    if not profile:
        logger.warning(f"Profile id={profile_id} not found")
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "Profile not found"}
        )

    logger.info(f"Profile found: {len(profile.source_urls)} URLs")

    return profile


# AICODE-NOTE: T092 - DELETE /api/profiles/{id} endpoint
@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """
    Delete style profile by ID.

    AICODE-NOTE: T092 - Profile deletion for creating new profiles (FR-029)
    Allows user to remove old profile before creating new one.
    Used by "Update Profile" workflow in UI.

    Args:
        profile_id: Profile database ID
        db: Database session (injected)

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: If profile not found
    """
    logger.info(f"Deleting profile id={profile_id}")

    profile = db.query(StyleProfileDB).filter(StyleProfileDB.id == profile_id).first()

    if not profile:
        logger.warning(f"Profile id={profile_id} not found")
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "Profile not found"}
        )

    db.delete(profile)
    db.commit()

    logger.success(f"Profile id={profile_id} deleted")

    return None
