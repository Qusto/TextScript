"""LLM client for OpenRouter API."""

from openai import OpenAI
from loguru import logger

# AICODE-NOTE: OpenRouter API endpoint configuration
# We use OpenRouter with the OpenAI SDK instead of direct API calls because:
# 1. OpenRouter provides OpenAI-compatible API at https://openrouter.ai/api/v1
# 2. No need for custom HTTP client - reuse battle-tested openai library
# 3. Same interface as OpenAI: client.chat.completions.create()
# 4. Easy to switch models: just change model string (e.g., "anthropic/claude-3.5-sonnet")
# 5. OpenRouter handles routing to multiple LLM providers (Anthropic, OpenAI, etc.)
# This approach minimizes custom code while maximizing flexibility


class LLMClient:
    """Client for interacting with LLM via OpenRouter API.

    Uses OpenAI SDK with OpenRouter base URL for compatibility.
    """

    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        """Initialize LLM client with OpenRouter configuration.

        Args:
            api_key: OpenRouter API key
            model: Model identifier (default: claude-3.5-sonnet)
        """
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def analyze_style(self, content: str) -> str:
        """Analyze writing style from content.

        Args:
            content: Text content to analyze

        Returns:
            Style analysis description from LLM

        Raises:
            Exception: If API call fails
        """
        prompt = f"""Analyze the writing style of the following text. Describe the author's:
- Tone and voice
- Sentence structure and rhythm
- Vocabulary choices
- Use of rhetorical devices
- Overall stylistic characteristics

Text to analyze:
{content}

Provide a detailed style analysis that could be used to replicate this writing style."""

        logger.info("Analyzing writing style...")
        response = self.client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    def generate_article(self, topic: str, style_profile: str) -> str:
        """Generate article on topic using specified style.

        Args:
            topic: Article topic
            style_profile: Style description to emulate

        Returns:
            Generated article text

        Raises:
            Exception: If API call fails
        """
        prompt = f"""Write an article about "{topic}" in the following writing style:

{style_profile}

Generate a well-structured article that matches this style profile."""

        logger.info(f"Generating article about '{topic}'...")
        response = self.client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content
