"""Research client for enriching articles with facts, quotes, and current data."""

import re
from datetime import datetime
from loguru import logger

from src.models import StyleHints, ResearchResult
from src.config import Configuration
from src.llm_client import LLMClient
from src.prompt_manager import PromptManager


# AICODE-NOTE: Why use Perplexity Sonar via OpenRouter for research?
# We chose Perplexity Sonar (accessed via OpenRouter) instead of direct web scraping because:
# 1. Real-time search: Sonar provides current information from live web sources
# 2. Summarization: Automatically synthesizes information from multiple sources
# 3. Citation: Returns information with source attribution (quotes, studies)
# 4. Specialized: Sonar models are optimized for research/search tasks
# 5. Same API: Accessed through OpenRouter, no separate integration needed
# 6. Cost-effective: perplexity/sonar-pro is cheaper than GPT-4 for research tasks
# Trade-off: Adds API cost, but ensures articles have accurate, current information
# Alternative considered: Direct web scraping + summarization (complex, error-prone)


class ResearchClient:
    """Client for performing research using Perplexity Sonar via OpenRouter.

    Uses LLM with real-time search capabilities to gather facts, statistics,
    quotes, and current information to enrich article generation.
    """

    def __init__(self, config: Configuration, llm_client: LLMClient | None = None):
        """Initialize research client with configuration.

        Args:
            config: Application configuration with API settings
            llm_client: Optional LLMClient instance (or CostTracker wrapper).
                       If not provided, creates a new LLMClient.
        """
        self.config = config
        self.llm_client = llm_client or LLMClient(
            api_key=config.api_key, model=config.model
        )
        self.prompt_manager = PromptManager()

    def research(self, topic: str, style_hints: StyleHints) -> ResearchResult:
        """Perform research on topic guided by style hints.

        Args:
            topic: Research topic/question
            style_hints: Author's content preferences to guide research

        Returns:
            ResearchResult with facts, quotes, and full research text

        Raises:
            Exception: If API call fails
        """
        logger.info(f"Researching topic: '{topic}'")
        logger.debug(
            f"Style hints: depth={style_hints.content_depth}, "
            f"tech={style_hints.technical_level}, "
            f"sources={style_hints.preferred_sources}"
        )

        # Load prompt template
        prompt_template = self.prompt_manager.load_prompt(
            "research",
            default=self._get_default_prompt(),
        )

        # Render prompt with topic and style hints
        prompt = prompt_template.format(
            topic=topic,
            content_depth=style_hints.content_depth,
            technical_level=style_hints.technical_level,
            preferred_sources=style_hints.preferred_sources,
            focus_areas=", ".join(style_hints.focus_areas),
        )

        # Call LLM with research model
        logger.debug(f"Using research model: {self.config.research_model}")

        # Check if llm_client is CostTracker (has stage_name parameter)
        if hasattr(self.llm_client, "generation_ids"):
            response = self.llm_client.generate(
                prompt, model=self.config.research_model, stage_name="research"
            )
        else:
            response = self.llm_client.generate(
                prompt, model=self.config.research_model
            )

        logger.debug(f"Research response length: {len(response)} chars")

        # Parse response into structured result
        result = self._parse_research_response(response, topic)

        logger.info(
            f"Research complete: {len(result.facts_and_stats)} facts, "
            f"{len(result.quotes_and_sources)} quotes"
        )

        return result

    def _parse_research_response(
        self, response: str, topic: str
    ) -> ResearchResult:
        """Parse LLM research response into structured ResearchResult.

        Args:
            response: Raw research text from LLM
            topic: Original research topic

        Returns:
            ResearchResult with parsed sections
        """
        facts_and_stats = self._extract_facts(response)
        quotes_and_sources = self._extract_quotes(response)

        return ResearchResult(
            topic=topic,
            facts_and_stats=facts_and_stats,
            quotes_and_sources=quotes_and_sources,
            full_research_text=response.strip(),
            sources_count=len(quotes_and_sources),
            timestamp=datetime.now(),
        )

    def _extract_facts(self, text: str) -> list[str]:
        """Extract facts and statistics from research text.

        Looks for section like "## Key Facts and Statistics" and extracts
        bullet points.

        Args:
            text: Research text

        Returns:
            List of fact strings
        """
        # Find "Key Facts and Statistics" section
        facts_match = re.search(
            r"##\s*Key Facts and Statistics\s*\n(.*?)(?=\n##|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if not facts_match:
            return []

        section = facts_match.group(1)

        # Extract bullet points
        facts = re.findall(r"^\s*[-*]\s*(.+)$", section, re.MULTILINE)

        # Clean up facts
        facts = [f.strip() for f in facts if f.strip()]

        return facts

    def _extract_quotes(self, text: str) -> list[dict[str, str]]:
        """Extract quotes and sources from research text.

        Looks for section like "## Expert Quotes and Sources" and extracts
        bullet points as dictionaries.

        Args:
            text: Research text

        Returns:
            List of quote dictionaries with 'text' key
        """
        # Find "Expert Quotes and Sources" section
        quotes_match = re.search(
            r"##\s*Expert Quotes and Sources\s*\n(.*?)(?=\n##|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if not quotes_match:
            return []

        section = quotes_match.group(1)

        # Extract bullet points
        quote_lines = re.findall(r"^\s*[-*]\s*(.+)$", section, re.MULTILINE)

        # Convert to dict format
        quotes = [{"text": q.strip()} for q in quote_lines if q.strip()]

        return quotes

    def _get_default_prompt(self) -> str:
        """Get default research prompt template if file doesn't exist.

        Returns:
            Default prompt template string
        """
        return """Research the following topic and provide comprehensive, current information.

TOPIC: {topic}

STYLE GUIDANCE:
- Content depth preference: {content_depth}
- Technical level: {technical_level}
- Preferred source types: {preferred_sources}
- Focus areas: {focus_areas}

Please structure your research as follows:

## Key Facts and Statistics
- [Bullet point with specific data, numbers, percentages]
- [Another fact with concrete details]
- [3-5 key facts total]

## Expert Quotes and Sources
- [Quote or finding from credible source with attribution]
- [Another quote or study with source]
- [2-4 quotes/sources total]

## Full Research Synthesis
[Comprehensive paragraph(s) synthesizing the research, integrating facts and sources
into a cohesive narrative. Match the content_depth and technical_level preferences.]

Focus on:
1. Current, up-to-date information (prefer recent sources)
2. Credible sources matching the preferred_sources type
3. Concrete facts and data points for content_depth={content_depth}
4. Technical complexity matching technical_level={technical_level}
5. Topics related to: {focus_areas}

Ensure all information is accurate and properly attributed."""
