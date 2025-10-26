"""Data models and entities."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class URLSource:
    """Represent a single URL and its fetched content.

    Attributes:
        url: Original URL from links.txt
        content: Extracted text content (None if fetch failed)
        status: Fetch status ('success' or 'failed')
        error: Error message if status == 'failed'
    """

    url: str
    content: str | None = None
    status: Literal["success", "failed"] = "failed"
    error: str | None = None

    @property
    def char_count(self) -> int:
        """Return character count of content."""
        return len(self.content) if self.content else 0

    def truncate(self, max_length: int) -> None:
        """Truncate content to max_length characters.

        Args:
            max_length: Maximum number of characters to keep
        """
        if self.content and len(self.content) > max_length:
            self.content = self.content[:max_length]


@dataclass
class ContentCollection:
    """Aggregate content from multiple URLSource instances.

    Attributes:
        sources: List of fetched URL sources
    """

    sources: list[URLSource]

    @property
    def combined_content(self) -> str:
        """Concatenate all successful source content with double newlines."""
        return "\n\n".join(
            source.content
            for source in self.sources
            if source.status == "success" and source.content
        )

    @property
    def total_chars(self) -> int:
        """Return total character count of combined content."""
        return len(self.combined_content)

    @property
    def success_count(self) -> int:
        """Return number of successfully fetched URLs."""
        return sum(1 for s in self.sources if s.status == "success")

    @property
    def failure_count(self) -> int:
        """Return number of failed URLs."""
        return sum(1 for s in self.sources if s.status == "failed")

    def truncate_to_limit(self, max_total: int) -> None:
        """Truncate combined content to max_total characters.

        Uses simple slice approach for v0.0.1 - just truncates the combined
        string at the limit rather than proportional truncation of sources.

        Args:
            max_total: Maximum total characters for combined content
        """
        # AICODE-NOTE: Truncation strategy decision for v0.0.1
        # We chose simple slice truncation over proportional source truncation because:
        # 1. Simplicity: Meets 90-minute development constraint
        # 2. Predictable: Always preserves first N characters deterministically
        # 3. Good enough: For style analysis, having complete early content is often
        #    more valuable than partial content from all sources
        # 4. No complex math: Proportional truncation would need to calculate per-source
        #    limits, handle rounding, and update multiple sources
        # Future: Could implement proportional truncation if users need representative
        # samples from all sources (e.g., when URLs have very different styles)
        if self.total_chars > max_total:
            # Get combined content and truncate it
            combined = self.combined_content[:max_total]

            # Update sources to reflect truncation
            # Strategy: Keep sources as-is but rebuild from truncated combined
            # For simplicity, we replace sources with a single synthetic source
            self.sources = [
                URLSource(
                    url="[truncated_collection]",
                    content=combined,
                    status="success",
                )
            ]


@dataclass
class StyleProfile:
    """Store analyzed writing style characteristics.

    Attributes:
        profile_text: LLM-generated style analysis
        source_urls: URLs used for analysis
        url_hash: MD5 hash of sorted URLs (cache key)
        cached: True if loaded from cache, False if freshly generated
    """

    profile_text: str
    source_urls: list[str]
    url_hash: str
    cached: bool = False

    @property
    def cache_filename(self) -> str:
        """Return cache file path."""
        return f"style_profiles/{self.url_hash}.txt"


@dataclass
class GeneratedArticle:
    """Represent the final generated article output.

    Attributes:
        content: Article text from LLM
        topic: Original topic from topic.txt
        style_hash: Hash of source URLs (links to StyleProfile)
    """

    content: str
    topic: str
    style_hash: str

    @property
    def word_count(self) -> int:
        """Calculate word count."""
        return len(self.content.split())

    def print_to_stdout(self) -> None:
        """Print article to console."""
        print("\n--- YOUR ARTICLE ---")
        print(self.content)

    def save_to_file(self, filename: str = "output.txt") -> None:
        """Save article content to file.

        Args:
            filename: Output file path (default: output.txt)
        """
        from pathlib import Path
        from loguru import logger

        output_path = Path(filename)

        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            output_path.write_text(self.content, encoding="utf-8")
            logger.debug(f"Saved article to {filename}")
        except Exception as e:
            logger.error(f"Failed to save article to {filename}: {e}")
            raise
