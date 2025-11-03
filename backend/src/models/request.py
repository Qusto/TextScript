"""
Request models for article generation API.

AICODE-NOTE: T032 - Pydantic models for input validation with custom validators.
Validates topic length (1-1000 chars) and URLs (valid HTTP/HTTPS, 1-10 count).
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, HttpUrl


class GenerateArticleRequest(BaseModel):
    """
    Article generation request parameters (legacy GET endpoint).

    AICODE-NOTE: T032 - Comprehensive input validation for FR-032.
    - topic: 1-1000 characters
    - source_urls: 1-10 valid HTTP/HTTPS URLs
    - research: optional boolean flag

    DEPRECATED: Use GenerateArticleRequestV2 for POST endpoint (T104)
    """

    topic: Annotated[
        str,
        Field(
            min_length=1,
            max_length=1000,
            description="Article topic (1-1000 characters)"
        )
    ]

    source_urls: Annotated[
        str,
        Field(
            description="Source URLs (newline or comma separated, 1-10 URLs)"
        )
    ]

    research: bool = Field(
        default=False,
        description="Enable research mode"
    )

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """
        Validate topic string.

        AICODE-NOTE: Additional validation beyond length constraints.
        Ensure topic is not just whitespace.
        """
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty or whitespace only")
        return v.strip()

    @field_validator("source_urls")
    @classmethod
    def validate_source_urls(cls, v: str) -> str:
        """
        Validate source URLs.

        AICODE-NOTE: T032 - Parse and validate URLs:
        1. Split by newline or comma
        2. Validate each URL is valid HTTP/HTTPS
        3. Ensure 1-10 URLs total

        Args:
            v: Raw URLs string (newline or comma separated)

        Returns:
            Validated URLs string

        Raises:
            ValueError: If validation fails
        """
        if not v or not v.strip():
            raise ValueError("At least one source URL is required")

        # AICODE-NOTE: Split by both newline and comma for flexibility
        # First split by newlines, then by commas
        urls = []
        for line in v.split("\n"):
            for url in line.split(","):
                url = url.strip()
                if url:
                    urls.append(url)

        # AICODE-NOTE: Check URL count (1-10)
        if len(urls) < 1:
            raise ValueError("At least one source URL is required")

        if len(urls) > 10:
            raise ValueError(
                f"Maximum 10 URLs allowed, got {len(urls)}. "
                "Please reduce the number of source URLs."
            )

        # AICODE-NOTE: T048 - Enhanced URL validation with security checks
        # Reject shell/command injection characters
        dangerous_chars = ['`', '$', '|', '<', '>', '\\', '{', '}']

        for url in urls:
            # AICODE-NOTE: T048 - Check for shell injection characters
            # These characters could be used in command injection attacks
            for char in dangerous_chars:
                if char in url:
                    raise ValueError(
                        f"Invalid URL format: {url}. "
                        f"URLs cannot contain shell metacharacters: {', '.join(dangerous_chars)}"
                    )

            # AICODE-NOTE: T048 - Check for SQL injection patterns
            if "'" in url and any(keyword in url.upper() for keyword in ['DROP', 'DELETE', 'INSERT', 'UPDATE', '--']):
                raise ValueError(
                    f"Invalid URL format: {url}. "
                    "URLs with SQL injection patterns are not allowed"
                )

            # AICODE-NOTE: Validate URL pattern (HTTP/HTTPS only)
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?][\w\-\.~:/?#\[\]@!&\'()*+,;=%]*)?$',  # path (RFC 3986 safe chars)
                re.IGNORECASE
            )

            if not url_pattern.match(url):
                raise ValueError(
                    f"Invalid URL format: {url}. "
                    "URLs must start with http:// or https://"
                )

        # AICODE-NOTE: Return validated URLs (keep original format)
        return v

    model_config = {
        # AICODE-NOTE: Pydantic V2 uses model_config instead of Config class
        "str_strip_whitespace": True
    }


class GenerateArticleRequestV2(BaseModel):
    """
    Article generation request for POST endpoint (Phase 10).

    AICODE-NOTE: T104 - New request model for two-stage generation with style profiles.
    AICODE-NOTE: T123 - Made profileId optional to support free-style generation.
    - title: Article title (required, 1-1000 chars)
    - keyPoints: Optional key points for article content
    - profileId: Style profile ID from database (optional, None for free style)
    - enableResearch: Two-stage research mode flag
    """

    title: Annotated[
        str,
        Field(
            min_length=1,
            max_length=1000,
            description="Article title (1-1000 characters)"
        )
    ]

    keyPoints: Annotated[
        str | None,
        Field(
            default=None,
            max_length=5000,
            description="Optional key points for article (max 5000 characters)"
        )
    ]

    profileId: Annotated[
        int | None,
        Field(
            default=None,
            gt=0,
            description="Style profile ID from database (optional, None for free style)"
        )
    ]

    enableResearch: bool = Field(
        default=False,
        description="Enable two-stage research mode"
    )

    wordCount: Annotated[
        int,
        Field(
            default=500,
            ge=100,
            le=5000,
            description="Target article length in words (100-5000, ±10-20% accuracy)"
        )
    ]

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """
        Validate title string.

        AICODE-NOTE: Ensure title is not just whitespace.
        """
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()

    @field_validator("keyPoints")
    @classmethod
    def validate_key_points(cls, v: str | None) -> str | None:
        """
        Validate key points string.

        AICODE-NOTE: T106 - Optional field validation.
        Strip whitespace, return None if empty.
        """
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None

    model_config = {
        # AICODE-NOTE: Pydantic V2 uses model_config instead of Config class
        "str_strip_whitespace": True
    }
