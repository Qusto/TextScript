"""Extract style hints from style profiles to guide research queries."""

import json
from typing import Literal
from loguru import logger

from src.models import StyleProfile, StyleHints
from src.config import Configuration
from src.llm_client import LLMClient
from src.prompt_manager import PromptManager


# AICODE-NOTE: Why use LLM for style hints extraction instead of keyword matching?
# We chose LLM-based extraction over simple keyword/regex matching because:
# 1. Accuracy: Style profiles are natural language - LLMs understand nuance and context
# 2. Consistency: LLM can map varied descriptions to our Literal types reliably
#    (e.g., "uses simple words" → technical_level="simple")
# 3. Robustness: Works with any style profile format, not just specific keywords
# 4. Multi-dimensional: Extracts multiple orthogonal hints simultaneously
# 5. Cost-effective: One small API call per profile (and profiles are cached anyway)
# Trade-off: Adds ~1-2 seconds and minimal API cost, but ensures research quality
# Future: Could add keyword fallback if LLM extraction fails


class StyleHintsExtractor:
    """Extract content preferences from style profiles.

    Uses LLM to analyze a style profile and extract structured hints
    about the author's preferred content type, technical level, sources, etc.
    """

    def __init__(
        self, config: Configuration, llm_client: LLMClient | None = None
    ):
        """Initialize extractor with configuration.

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

    def extract(self, style_profile: StyleProfile) -> StyleHints:
        """Extract style hints from a style profile.

        Sends the style profile text to an LLM with a structured prompt
        to extract content preferences as JSON.

        Args:
            style_profile: Style profile to analyze

        Returns:
            StyleHints with extracted preferences, or defaults if extraction fails
        """
        logger.debug(f"Extracting style hints from profile (hash: {style_profile.url_hash})")

        # Load prompt template
        prompt_template = self.prompt_manager.load_prompt(
            "research_style_hints",
            default=self._get_default_prompt(),
        )

        # Render prompt with profile text
        prompt = prompt_template.format(profile_text=style_profile.profile_text)

        # Call LLM
        try:
            # Check if llm_client is CostTracker (has stage_name parameter)
            if hasattr(self.llm_client, "generation_ids"):
                response = self.llm_client.generate(
                    prompt, stage_name="style_hints_extraction"
                )
            else:
                response = self.llm_client.generate(prompt)

            logger.debug(f"LLM response for style hints: {response[:200]}...")

            # Parse JSON response
            hints_data = self._parse_response(response)

            # Build StyleHints with validation
            hints = self._build_style_hints(hints_data)

            logger.info(
                f"Extracted style hints: depth={hints.content_depth}, "
                f"tech={hints.technical_level}, sources={hints.preferred_sources}"
            )

            return hints

        except Exception as e:
            logger.warning(f"Failed to extract style hints: {e}. Using defaults.")
            return StyleHints()  # Return defaults on any error

    def _parse_response(self, response: str) -> dict:
        """Parse LLM response as JSON.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed JSON as dict, or empty dict if parsing fails
        """
        try:
            # Try to find JSON in response (handle cases where LLM adds explanation)
            response = response.strip()

            # If response has markdown code blocks, extract JSON
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            return json.loads(response)

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {}

    def _build_style_hints(self, data: dict) -> StyleHints:
        """Build StyleHints from parsed data with validation.

        Args:
            data: Parsed JSON data from LLM

        Returns:
            StyleHints instance with validated values
        """
        # Valid literal values
        VALID_DEPTH = {"descriptive", "concrete", "balanced"}
        VALID_TECH = {"technical", "simple", "mixed"}
        VALID_SOURCES = {"academic", "practical", "varied"}

        # Extract and validate content_depth
        content_depth = data.get("content_depth", "balanced")
        if content_depth not in VALID_DEPTH:
            logger.warning(f"Invalid content_depth '{content_depth}', using 'balanced'")
            content_depth = "balanced"

        # Extract and validate technical_level
        technical_level = data.get("technical_level", "mixed")
        if technical_level not in VALID_TECH:
            logger.warning(f"Invalid technical_level '{technical_level}', using 'mixed'")
            technical_level = "mixed"

        # Extract and validate preferred_sources
        preferred_sources = data.get("preferred_sources", "varied")
        if preferred_sources not in VALID_SOURCES:
            logger.warning(f"Invalid preferred_sources '{preferred_sources}', using 'varied'")
            preferred_sources = "varied"

        # Extract and clean focus_areas
        focus_areas = data.get("focus_areas", ["data", "examples"])
        if not focus_areas or not isinstance(focus_areas, list):
            focus_areas = ["data", "examples"]
        else:
            # Clean and normalize focus areas
            focus_areas = [
                area.strip().lower()
                for area in focus_areas
                if isinstance(area, str) and area.strip()
            ]
            # Ensure we have at least some focus areas
            if not focus_areas:
                focus_areas = ["data", "examples"]

        return StyleHints(
            content_depth=content_depth,  # type: ignore
            technical_level=technical_level,  # type: ignore
            preferred_sources=preferred_sources,  # type: ignore
            focus_areas=focus_areas,
        )

    def _get_default_prompt(self) -> str:
        """Get default prompt template if file doesn't exist.

        Returns:
            Default prompt template string
        """
        return """Analyze this writing style profile and extract content preferences.

STYLE PROFILE:
{profile_text}

Extract the following preferences and return as JSON:

1. content_depth: Does the author prefer descriptive/narrative content or concrete facts/data?
   - "descriptive": Rich descriptions, metaphors, storytelling
   - "concrete": Facts, numbers, data points, brevity
   - "balanced": Mix of both

2. technical_level: What technical complexity does the author prefer?
   - "technical": Jargon, technical terms, assumes expertise
   - "simple": Plain language, explains concepts simply
   - "mixed": Balances technical accuracy with accessibility

3. preferred_sources: What types of sources fit this style?
   - "academic": Research papers, studies, scholarly sources
   - "practical": Case studies, real-world examples, industry reports
   - "varied": Mix of academic and practical sources

4. focus_areas: What topics or content types does the style emphasize? (list of strings)
   Examples: ["data visualization", "statistics", "tutorials", "case studies"]

Return ONLY valid JSON with these exact keys:
{
    "content_depth": "descriptive" | "concrete" | "balanced",
    "technical_level": "technical" | "simple" | "mixed",
    "preferred_sources": "academic" | "practical" | "varied",
    "focus_areas": ["area1", "area2", ...]
}"""
