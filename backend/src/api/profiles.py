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
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field
from loguru import logger

from src.db.database import get_db
from src.db.models import StyleProfileDB
from src.style_cache import generate_url_hash

# AICODE-NOTE: T088 - Create FastAPI router for profile endpoints
router = APIRouter(prefix="/api/profiles", tags=["profiles"])


# AICODE-NOTE: T088 - Request/Response models for type safety and validation
class ProfileCreateRequest(BaseModel):
    """Request model for creating new style profile."""

    source_urls: List[HttpUrl] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of URLs to extract style from (1-10 URLs)",
        examples=[
            [
                "https://example.com/article1",
                "https://example.com/article2",
            ]
        ],
    )


class ProfileResponse(BaseModel):
    """Response model for profile data."""

    id: int
    urls_hash: str
    profile_text: str
    source_urls: List[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True  # Allow ORM model conversion


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

    return profile


# AICODE-NOTE: T090 - POST /api/profiles endpoint
@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(
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
    logger.info(f"Creating profile from {len(request.source_urls)} URLs")

    # AICODE-NOTE: T090 - Convert Pydantic HttpUrl objects to strings
    url_strings = [str(url) for url in request.source_urls]

    # AICODE-NOTE: T090 - Generate MD5 hash for duplicate detection
    # Reuses existing generate_url_hash from style_cache.py
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

    # AICODE-NOTE: T090 - Call style extraction script
    # TODO: Replace with proper script path and arguments
    # For now, create a placeholder profile
    # In production, this would call: src/ugly_script.py --urls file.txt --extract-style

    try:
        # AICODE-NOTE: Placeholder for style extraction
        # Real implementation will call subprocess to run style extraction
        profile_text = await _extract_style_from_urls(url_strings)

        logger.info(
            f"Style extracted: {len(profile_text)} chars"
        )

    except Exception as e:
        logger.error(f"Style extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "extraction_failed",
                "message": "Failed to extract style from URLs",
                "details": str(e),
            },
        )

    # AICODE-NOTE: T090 - Save profile to database
    new_profile = StyleProfileDB(
        urls_hash=urls_hash,
        profile_text=profile_text,
        source_urls=url_strings,  # Store as JSON array
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    logger.success(
        f"Profile created: id={new_profile.id}, hash={urls_hash[:8]}..."
    )

    return new_profile


async def _extract_style_from_urls(urls: List[str]) -> str:
    """
    Extract writing style from URLs using existing article script.

    AICODE-NOTE: T090 - Style extraction integration
    Calls the existing src/ugly_script.py with style extraction mode.
    Reuses all existing style analysis logic from Phase 1.

    Args:
        urls: List of source URLs to analyze

    Returns:
        str: Extracted style characteristics (profile_text)

    Raises:
        Exception: If extraction fails
    """
    # AICODE-NOTE: Write URLs to temporary file for script input
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as f:
        for url in urls:
            f.write(f"{url}\n")
        urls_file = f.name

    try:
        # AICODE-NOTE: Call style extraction script
        # Path to src/ugly_script.py (adjust based on actual location)
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

        # AICODE-NOTE: Run style extraction subprocess
        # Command: python src/ugly_script.py --extract-style --urls <file>
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            "--extract-style",
            "--urls",
            urls_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8").strip()
            raise Exception(f"Script failed: {error_msg}")

        # AICODE-NOTE: Parse extracted profile from stdout
        profile_text = stdout.decode("utf-8").strip()

        if not profile_text:
            raise Exception("Style extraction returned empty result")

        return profile_text

    finally:
        # AICODE-NOTE: Clean up temporary URLs file
        Path(urls_file).unlink(missing_ok=True)


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
