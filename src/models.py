"""Data models and entities."""

from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime


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


@dataclass
class StyleHints:
    """Author's content preferences extracted from style profile.

    Used to guide research queries toward author's preferred content type.

    Attributes:
        content_depth: Preference for descriptive details vs concrete facts
        technical_level: Preference for technical jargon vs simple language
        preferred_sources: Types of sources that fit the style
        focus_areas: What types of information the style emphasizes
    """

    content_depth: Literal["descriptive", "concrete", "balanced"] = "balanced"
    technical_level: Literal["technical", "simple", "mixed"] = "mixed"
    preferred_sources: Literal["academic", "practical", "varied"] = "varied"
    focus_areas: list[str] = field(default_factory=lambda: ["data", "examples"])


# AICODE-NOTE: Research is NOT cached (unlike style profiles)
# We deliberately don't cache research results because:
# 1. Research data becomes outdated - facts, statistics, and news change
# 2. User explicitly chose "always do fresh research" for current information
# 3. Research API (Perplexity Sonar) provides real-time web search results
# 4. Style profiles are static (author's writing pattern), but research is dynamic
# 5. Caching by topic would be complex (same topic, different angles/depth)
# Trade-off: Extra API cost for freshness, but ensures articles have current data
# Future: Could add optional research cache with TTL if cost becomes issue


@dataclass
class ResearchResult:
    """Result from research API containing enrichment data for article.

    Attributes:
        topic: Original research topic
        facts_and_stats: Key facts with data points
        quotes_and_sources: Expert quotes with attribution
        full_research_text: Comprehensive research synthesis
        sources_count: Number of sources consulted
        timestamp: When research was performed
    """

    topic: str
    facts_and_stats: list[str] = field(default_factory=list)
    quotes_and_sources: list[dict[str, str]] = field(default_factory=list)
    full_research_text: str = ""
    sources_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GenerationCost:
    """Cost information for a single API call to OpenRouter.

    Attributes:
        model: Model identifier used for generation
        prompt_tokens: Number of tokens in prompt (native count)
        completion_tokens: Number of tokens in completion (native count)
        total_tokens: Total tokens used
        cost_usd: Cost in USD dollars
        generation_id: OpenRouter generation ID
        stage: Stage name (e.g., "style_analysis", "research", "article_generation")
    """

    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    generation_id: str
    stage: str


@dataclass
class ArticleCostReport:
    """Aggregated cost report for article generation.

    Attributes:
        costs: List of individual generation costs
    """

    costs: list[GenerationCost] = field(default_factory=list)

    @property
    def total_cost_usd(self) -> float:
        """Calculate total cost across all API calls."""
        return sum(c.cost_usd for c in self.costs)

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens across all API calls."""
        return sum(c.total_tokens for c in self.costs)

    def print_report(self) -> None:
        """Print detailed cost report to console."""
        from loguru import logger

        if not self.costs:
            logger.info("No API calls tracked (possibly all cached)")
            return

        logger.info("")
        logger.info("=== Cost Report ===")

        # Print each stage
        for cost in self.costs:
            logger.info(
                f"  {cost.stage}: ${cost.cost_usd:.2f} "
                f"({cost.total_tokens} tokens, model: {cost.model})"
            )

        # Print total
        logger.info("  " + "-" * 50)
        logger.success(
            f"  Total cost: ${self.total_cost_usd:.2f} "
            f"({self.total_tokens} total tokens)"
        )
