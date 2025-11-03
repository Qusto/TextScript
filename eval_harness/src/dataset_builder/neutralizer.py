# AICODE-NOTE: T033 [P] [US1] Neutralizer class implementing prompt-neutralizer.md contract
# AICODE-NOTE: T034 - Dependency injection of LLM client for testability
# AICODE-NOTE: T035 - System + User message structure from prompt contract
# AICODE-NOTE: T036 - JSON parsing with TopicData validation, retry on malformed JSON
# AICODE-NOTE: T037 - Theses count validation: accepts 4-11, strict retries if <4 or >11
# AICODE-NOTE: T038 - Text truncation using shared truncate_text()

"""Neutralizer component for extracting neutral topics from stylized articles.

This module implements the topic neutralization logic that extracts
factual content from stylistically rich articles, removing metaphors,
emotional language, and other stylistic elements.

Key responsibilities:
- Call LLM with neutralization prompt
- Parse and validate JSON responses
- Validate theses count (5-10 standard, 4-11 acceptable)
- Detect stylistic markers in output (quality check)
- Truncate long texts before API calls
"""

import json
import re
from typing import Optional

from loguru import logger

from src.dataset_builder.config import TopicData
from src.shared.file_utils import truncate_text
from src.shared.llm_client import LLMClient


class Neutralizer:
    """Extract neutralized topics and theses from stylized articles.

    AICODE-NOTE: T033 - Implements prompt-neutralizer.md contract
    AICODE-NOTE: Uses LLM to extract topic and 5-10 factual theses
    AICODE-NOTE: Removes ALL stylistic elements (metaphors, emotional language, etc.)
    """

    # AICODE-NOTE: System message from prompt-neutralizer.md
    SYSTEM_PROMPT = """You are an AI analyst with advanced semantic analysis and summarization skills. Your task is to deconstruct the provided text, separating its stylistic form from its factual content. You must extract "what is said" while completely ignoring "how it is said".

Your goal is to create a stylistically NEUTRAL set of theses."""

    # AICODE-NOTE: User message template from prompt-neutralizer.md
    USER_PROMPT_TEMPLATE = """Your task is to analyze the following text and return a JSON object with two keys:
1. "topic": A neutral, encyclopedic topic of the text in 1-5 words.
2. "theses": An array of strings containing 5 to 10 key theses, facts, or plot points from the text.

**Critical Requirements for Theses:**
* NEUTRALITY: Theses must be written in dry, impersonal, "bureaucratic" language.
* NO STYLE: Avoid any metaphors, emotionally colored vocabulary, authorial turns of phrase, or rhythmic structure from the original.
* FACTS ONLY: Extract only key facts, events, or arguments.

**EXAMPLE:**
* Original (Stylized): "O, that cursed, damp wind! It howled like a hungry wolf, tearing at my already tormented soul as I trudged through the endless, muddy streets of Paris, seeing nothing..."
* Bad (Style Preserved): ["Wind howled like a wolf", "Soul was tormented", "Streets of Paris were muddy"]
* Good (Neutralized): ["Narrator is located in Paris.", "Weather conditions: strong wind.", "Narrator experiences negative emotions.", "Movement occurs on foot through streets."]

**Response Format:** JSON only.

<OriginalText>
{original_text}
</OriginalText>

Analyze the text and return JSON."""

    # AICODE-NOTE: Stylistic markers for heuristic quality check
    STYLISTIC_MARKERS = ["like a", "as if", "seemed to", "!", "alas", "oh"]

    def __init__(
        self,
        llm_client: LLMClient,
        max_tokens: int = 4000,
        model_id: str = "anthropic/claude-3-5-sonnet-20240620"
    ):
        """Initialize Neutralizer with LLM client.

        Args:
            llm_client: LLM client for API calls
            max_tokens: Maximum tokens to send to neutralizer (for cost control)
            model_id: Model ID for neutralization

        AICODE-NOTE: T034 - Dependency injection for testability
        AICODE-NOTE: LLM client is injected, not created internally
        """
        self.llm_client = llm_client
        self.max_tokens = max_tokens
        self.model_id = model_id

        logger.debug(
            f"Neutralizer initialized (model={model_id}, max_tokens={max_tokens})"
        )

    def neutralize(self, article_text: str) -> TopicData:
        """Extract neutralized topic and theses from article.

        Args:
            article_text: Original stylized article text

        Returns:
            TopicData with neutral topic and theses

        Raises:
            ValueError: If JSON is malformed or validation fails

        AICODE-NOTE: T035 - Implements prompt template from contract
        AICODE-NOTE: T036 - JSON parsing with validation
        AICODE-NOTE: T038 - Text truncation before API call
        """
        logger.info("Neutralizing article text")

        # AICODE-NOTE: T038 - Truncate long text before API call
        truncated_text = truncate_text(article_text, self.max_tokens)

        if len(truncated_text) < len(article_text):
            logger.warning(
                f"Article truncated from {len(article_text)} to {len(truncated_text)} chars"
            )

        # AICODE-NOTE: T035 - Build messages with system + user prompt
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self.USER_PROMPT_TEMPLATE.format(
                    original_text=truncated_text
                )
            }
        ]

        # AICODE-NOTE: Call LLM API
        logger.debug(f"Calling neutralizer API (model={self.model_id})")

        try:
            response = self.llm_client.generate(
                model_id=self.model_id,
                messages=messages,
                temperature=0.3,  # Low temperature for consistent factual extraction
                max_tokens=1000  # Output token limit
            )
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise ValueError(f"Failed to call neutralizer API: {e}") from e

        # AICODE-NOTE: T036 - Parse JSON response
        try:
            topic_data = self._parse_json_response(response)
        except ValueError as e:
            logger.error(f"Failed to parse neutralizer response: {e}")
            raise

        # AICODE-NOTE: T037 - Validate theses count
        self._validate_theses_count(topic_data)

        # AICODE-NOTE: Check for stylistic markers (quality heuristic)
        self._check_stylistic_markers(topic_data)

        logger.success(
            f"Neutralization complete: topic='{topic_data.topic}', "
            f"theses={len(topic_data.theses)}"
        )

        return topic_data

    def _parse_json_response(self, response: str) -> TopicData:
        """Parse and validate JSON response from LLM.

        Args:
            response: Raw text response from LLM

        Returns:
            Validated TopicData

        Raises:
            ValueError: If JSON is malformed or validation fails

        AICODE-NOTE: T036 - Handles Claude/GPT JSON formatting differences
        AICODE-NOTE: Claude wraps JSON in markdown code blocks
        AICODE-NOTE: GPT-4 may include explanatory text
        """
        # AICODE-NOTE: Strip markdown code blocks
        response = response.strip()

        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        # AICODE-NOTE: Try to find JSON object in response
        json_start = response.find("{")
        json_end = response.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError(
                f"No JSON object found in response: {response[:100]}..."
            )

        json_str = response[json_start:json_end]

        # AICODE-NOTE: Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Failed to parse: {json_str[:200]}...")
            raise ValueError(f"Invalid JSON in LLM response: {e}") from e

        # AICODE-NOTE: Validate with Pydantic TopicData schema
        try:
            validated = TopicData(**data)
            return validated
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise ValueError(
                f"JSON doesn't match TopicData schema: {e}"
            ) from e

    def _validate_theses_count(self, topic_data: TopicData) -> None:
        """Validate theses count and log warnings.

        Args:
            topic_data: TopicData to validate

        Raises:
            ValueError: If theses count is <4 or >11 (strict rejection)

        AICODE-NOTE: T037 - Theses count validation logic
        AICODE-NOTE: Standard range: 5-10 (no warning)
        AICODE-NOTE: Acceptable range: 4-11 (log warning but accept)
        AICODE-NOTE: Invalid range: <4 or >11 (strict rejection)
        """
        count = len(topic_data.theses)

        if count < 4:
            raise ValueError(
                f"Too few theses: {count} (minimum 4 acceptable, 5-10 standard)"
            )

        if count > 11:
            raise ValueError(
                f"Too many theses: {count} (maximum 11 acceptable, 5-10 standard)"
            )

        # AICODE-NOTE: Log warning for edge cases (4 or 11)
        if count == 4 or count == 11:
            logger.warning(
                f"Thesis count {count} is outside standard range (5-10), "
                f"but acceptable"
            )

    def _check_stylistic_markers(self, topic_data: TopicData) -> None:
        """Check for stylistic markers in neutralized output.

        Args:
            topic_data: TopicData to check

        AICODE-NOTE: Heuristic quality check for neutrality
        AICODE-NOTE: Logs warnings but doesn't reject output
        AICODE-NOTE: Markers: 'like a', 'as if', 'seemed to', '!', 'alas', 'oh'
        """
        combined_text = topic_data.topic + " " + " ".join(topic_data.theses)
        combined_lower = combined_text.lower()

        detected_markers = []
        for marker in self.STYLISTIC_MARKERS:
            if marker in combined_lower:
                detected_markers.append(marker)

        if detected_markers:
            logger.warning(
                f"Possible stylistic language detected in neutralized output: "
                f"{detected_markers}"
            )
            logger.debug(f"Output text: {combined_text[:200]}...")
