"""Configuration management."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Configuration:
    """Runtime configuration loaded from .env file with defaults.

    Attributes:
        api_key: OpenRouter API key (required)
        model: LLM model identifier (default: gpt-4o-mini)
        max_urls: Maximum number of URLs to process from links.txt
        max_content_per_url: Maximum characters to extract per URL
        max_total_content: Maximum total characters for style analysis
        url_fetch_timeout: HTTP request timeout in seconds
        research_enabled: Enable research stage before article generation
        research_model: Model to use for research (default: perplexity/sonar-pro)
    """

    api_key: str
    model: str = "openai/gpt-4o-mini"
    max_urls: int = 10
    max_content_per_url: int = 5000
    max_total_content: int = 8000
    url_fetch_timeout: int = 30
    research_enabled: bool = False
    research_model: str = "perplexity/sonar-pro"

    def __post_init__(self):
        """Validate configuration values."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        if self.max_urls <= 0:
            raise ValueError("MAX_URLS must be positive")
        if self.max_content_per_url <= 0:
            raise ValueError("MAX_CONTENT_LENGTH_PER_URL must be positive")
        if self.max_total_content <= 0:
            raise ValueError("MAX_TOTAL_CONTENT_LENGTH must be positive")
        if not (1 <= self.url_fetch_timeout <= 300):
            raise ValueError("URL_FETCH_TIMEOUT must be between 1-300 seconds")


def load_config(env_file: str = ".env") -> Configuration:
    """Load configuration from .env file with fallback to defaults.

    Returns:
        Configuration instance with validated values.

    Raises:
        ValueError: If required fields are missing or validation fails.
    """
    # AICODE-NOTE: Using python-dotenv instead of direct os.environ access for several reasons:
    # 1. Automatic .env file parsing and loading (no manual file reading)
    # 2. Non-intrusive: doesn't modify environment permanently, just makes vars available
    # 3. Standard pattern in Python projects for local development configuration
    # 4. Handles edge cases like quoted values, comments, and multiline values automatically
    # 5. Works seamlessly with both local .env files and production environment variables
    load_dotenv(dotenv_path=env_file, override=True)

    # Helper to safely convert env vars to int with fallback
    def get_int(key: str, default: int) -> int:
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    # Helper to safely convert env vars to bool
    def get_bool(key: str, default: bool) -> bool:
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    return Configuration(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("MODEL", "openai/gpt-4o-mini"),
        max_urls=get_int("MAX_URLS", 10),
        max_content_per_url=get_int("MAX_CONTENT_LENGTH_PER_URL", 5000),
        max_total_content=get_int("MAX_TOTAL_CONTENT_LENGTH", 8000),
        url_fetch_timeout=get_int("URL_FETCH_TIMEOUT", 30),
        research_enabled=get_bool("RESEARCH_ENABLED", False),
        research_model=os.getenv("RESEARCH_MODEL", "perplexity/sonar-pro"),
    )
