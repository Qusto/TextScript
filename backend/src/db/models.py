"""
Database models for style profile storage.

AICODE-NOTE: T087 - StyleProfileDB model definition (FR-028)
SQLAlchemy ORM model for persisting style profiles extracted from reference URLs.
Schema matches requirements from Phase 10 spec.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from src.db.database import Base


class StyleProfileDB(Base):
    """
    Style profile database model.

    AICODE-NOTE: T087 - Database table for style profile storage (FR-028)
    Stores extracted writing style characteristics for article generation.

    Schema:
    - id: Auto-increment primary key
    - urls_hash: MD5 hash of sorted source URLs (unique identifier, from style_cache.py)
    - profile_text: LLM-generated style analysis (used as generation prompt)
    - source_urls: JSON array of original URLs used for extraction
    - created_at: Timestamp of profile creation
    - updated_at: Timestamp of last update (auto-updated on changes)

    Example profile_text:
        "The author uses concise, data-driven language with technical terminology.
         Prefers bullet points and numbered lists. Includes specific statistics and
         examples to support arguments. Writing tone is professional and objective."

    Business Logic:
    - urls_hash ensures no duplicate profiles for same URL set
    - profile_text is the actual prompt used for article generation
    - source_urls stored as JSON for flexibility and query capability
    """

    __tablename__ = "style_profiles"

    # AICODE-NOTE: Primary key - auto-increment integer
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # AICODE-NOTE: Unique hash of source URLs (MD5 from generate_url_hash in style_cache.py)
    # Used to check if profile already exists for given URL set
    urls_hash = Column(
        String(32),  # MD5 hash is always 32 hex characters
        unique=True,
        nullable=False,
        index=True,
        comment="MD5 hash of sorted source URLs (cache key from style_cache.py)",
    )

    # AICODE-NOTE: LLM-generated style characteristics (main content)
    # This text is used as prompt guidance during article generation
    profile_text = Column(
        Text,
        nullable=False,
        comment="LLM-generated style analysis used for article generation prompt",
    )

    # AICODE-NOTE: Original source URLs as JSON array
    # Stored for display in UI and potential re-extraction
    # Example: ["https://example.com/article1", "https://example.com/article2"]
    source_urls = Column(
        JSON,
        nullable=False,
        comment="JSON array of original URLs used for style extraction",
    )

    # AICODE-NOTE: Timestamps for auditing and cache invalidation
    # created_at: Never changes after creation
    # updated_at: Auto-updates on any column modification (via onupdate)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Profile creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp (auto-updated on changes)",
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<StyleProfileDB(id={self.id}, "
            f"urls_hash={self.urls_hash[:8]}..., "
            f"urls_count={len(self.source_urls) if self.source_urls else 0}, "
            f"created_at={self.created_at})>"
        )

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses.

        AICODE-NOTE: T087 - Serialization for FastAPI JSON responses
        Converts SQLAlchemy model to dict for API endpoints.

        Returns:
            dict: Profile data with all fields
        """
        return {
            "id": self.id,
            "urls_hash": self.urls_hash,
            "profile_text": self.profile_text,
            "source_urls": self.source_urls,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
