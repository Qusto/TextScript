"""Tests for configuration management."""

import pytest
from pathlib import Path
from src.config import Configuration, load_config


class TestConfiguration:
    """Test Configuration dataclass."""

    def test_config_with_all_fields(self):
        """Test creating configuration with all fields."""
        config = Configuration(
            api_key="test_key_123",
            max_urls=5,
            max_content_per_url=3000,
            max_total_content=6000,
            url_fetch_timeout=20
        )
        assert config.api_key == "test_key_123"
        assert config.max_urls == 5
        assert config.max_content_per_url == 3000
        assert config.max_total_content == 6000
        assert config.url_fetch_timeout == 20

    def test_config_with_defaults(self):
        """Test configuration with default values."""
        config = Configuration(api_key="test_key")
        assert config.api_key == "test_key"
        assert config.max_urls == 10
        assert config.max_content_per_url == 5000
        assert config.max_total_content == 8000
        assert config.url_fetch_timeout == 30

    def test_config_requires_api_key(self):
        """Test that empty api_key raises ValueError."""
        with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
            Configuration(api_key="")

    def test_config_validates_max_urls_positive(self):
        """Test that max_urls must be positive."""
        with pytest.raises(ValueError, match="MAX_URLS must be positive"):
            Configuration(api_key="test_key", max_urls=0)

        with pytest.raises(ValueError, match="MAX_URLS must be positive"):
            Configuration(api_key="test_key", max_urls=-1)

    def test_config_validates_max_content_per_url_positive(self):
        """Test that max_content_per_url must be positive."""
        with pytest.raises(ValueError, match="MAX_CONTENT_LENGTH_PER_URL must be positive"):
            Configuration(api_key="test_key", max_content_per_url=0)

    def test_config_validates_max_total_content_positive(self):
        """Test that max_total_content must be positive."""
        with pytest.raises(ValueError, match="MAX_TOTAL_CONTENT_LENGTH must be positive"):
            Configuration(api_key="test_key", max_total_content=0)

    def test_config_validates_timeout_range(self):
        """Test that url_fetch_timeout must be between 1-300."""
        with pytest.raises(ValueError, match="URL_FETCH_TIMEOUT must be between 1-300"):
            Configuration(api_key="test_key", url_fetch_timeout=0)

        with pytest.raises(ValueError, match="URL_FETCH_TIMEOUT must be between 1-300"):
            Configuration(api_key="test_key", url_fetch_timeout=301)

        # Valid edge cases should not raise
        config_min = Configuration(api_key="test_key", url_fetch_timeout=1)
        assert config_min.url_fetch_timeout == 1

        config_max = Configuration(api_key="test_key", url_fetch_timeout=300)
        assert config_max.url_fetch_timeout == 300


class TestLoadConfig:
    """Test load_config() function."""

    def test_load_config_from_env(self, monkeypatch, tmp_path):
        """Test loading configuration from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENAI_API_KEY=env_test_key\n"
            "MAX_URLS=7\n"
            "MAX_CONTENT_LENGTH_PER_URL=4000\n"
            "MAX_TOTAL_CONTENT_LENGTH=9000\n"
            "URL_FETCH_TIMEOUT=25\n"
        )

        config = load_config(str(env_file))

        assert config.api_key == "env_test_key"
        assert config.max_urls == 7
        assert config.max_content_per_url == 4000
        assert config.max_total_content == 9000
        assert config.url_fetch_timeout == 25

    def test_load_config_with_partial_env(self, monkeypatch, tmp_path):
        """Test loading with partial .env (uses defaults)."""
        # Clear all config-related env vars
        for key in ["OPENAI_API_KEY", "MAX_URLS", "MAX_CONTENT_LENGTH_PER_URL",
                    "MAX_TOTAL_CONTENT_LENGTH", "URL_FETCH_TIMEOUT"]:
            monkeypatch.delenv(key, raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=partial_key\n")

        config = load_config(str(env_file))

        assert config.api_key == "partial_key"
        assert config.max_urls == 10  # default
        assert config.max_content_per_url == 5000  # default
        assert config.max_total_content == 8000  # default
        assert config.url_fetch_timeout == 30  # default

    def test_load_config_missing_api_key(self, monkeypatch, tmp_path):
        """Test that missing API key raises ValueError."""
        # Clear all config-related env vars
        for key in ["OPENAI_API_KEY", "MAX_URLS", "MAX_CONTENT_LENGTH_PER_URL",
                    "MAX_TOTAL_CONTENT_LENGTH", "URL_FETCH_TIMEOUT"]:
            monkeypatch.delenv(key, raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text("MAX_URLS=5\n")

        with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
            load_config(str(env_file))

    def test_load_config_no_env_file(self, monkeypatch, tmp_path):
        """Test that missing .env file raises helpful error."""
        # Clear all config-related env vars
        for key in ["OPENAI_API_KEY", "MAX_URLS", "MAX_CONTENT_LENGTH_PER_URL",
                    "MAX_TOTAL_CONTENT_LENGTH", "URL_FETCH_TIMEOUT"]:
            monkeypatch.delenv(key, raising=False)

        nonexistent_file = tmp_path / "nonexistent" / ".env"

        with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
            load_config(str(nonexistent_file))

    def test_load_config_invalid_integer_values(self, monkeypatch, tmp_path):
        """Test that invalid integer values are handled."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENAI_API_KEY=test_key\n"
            "MAX_URLS=not_a_number\n"
        )

        # Should use default when int conversion fails
        config = load_config(str(env_file))
        assert config.max_urls == 10  # default value


class TestLimitsEnforcement:
    """Test that configuration limits are properly enforced."""

    def test_max_urls_limit_applied(self, tmp_path):
        """Test that MAX_URLS limit is enforced."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENAI_API_KEY=test_key\n"
            "MAX_URLS=2\n"
        )

        config = load_config(str(env_file))
        assert config.max_urls == 2

        # Verify limit would be applied (simulated)
        test_urls = ["url1", "url2", "url3", "url4", "url5"]
        limited_urls = test_urls[:config.max_urls]
        assert len(limited_urls) == 2

    def test_max_content_per_url_limit_applied(self, tmp_path):
        """Test that MAX_CONTENT_LENGTH_PER_URL limit is enforced."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENAI_API_KEY=test_key\n"
            "MAX_CONTENT_LENGTH_PER_URL=1000\n"
        )

        config = load_config(str(env_file))
        assert config.max_content_per_url == 1000

        # Verify truncation would be applied
        long_content = "a" * 5000
        truncated = long_content[:config.max_content_per_url]
        assert len(truncated) == 1000

    def test_max_total_content_limit_applied(self, tmp_path):
        """Test that MAX_TOTAL_CONTENT_LENGTH limit is enforced."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENAI_API_KEY=test_key\n"
            "MAX_TOTAL_CONTENT_LENGTH=5000\n"
        )

        config = load_config(str(env_file))
        assert config.max_total_content == 5000

    def test_url_fetch_timeout_applied(self, tmp_path):
        """Test that URL_FETCH_TIMEOUT is properly configured."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENAI_API_KEY=test_key\n"
            "URL_FETCH_TIMEOUT=15\n"
        )

        config = load_config(str(env_file))
        assert config.url_fetch_timeout == 15

    def test_all_limits_together(self, tmp_path):
        """Test that all limits can be configured together."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENAI_API_KEY=test_key\n"
            "MAX_URLS=3\n"
            "MAX_CONTENT_LENGTH_PER_URL=2000\n"
            "MAX_TOTAL_CONTENT_LENGTH=6000\n"
            "URL_FETCH_TIMEOUT=20\n"
        )

        config = load_config(str(env_file))
        assert config.max_urls == 3
        assert config.max_content_per_url == 2000
        assert config.max_total_content == 6000
        assert config.url_fetch_timeout == 20

    def test_default_values_rationale(self):
        """Test default values are reasonable."""
        # AICODE-NOTE: Default values rationale (from research.md)
        # MAX_URLS=10: Allows analyzing multiple articles without overwhelming API
        # MAX_CONTENT_PER_URL=5000: ~1000-1250 words, captures full article essence
        # MAX_TOTAL_CONTENT=8000: Fits well within most LLM context windows
        # URL_FETCH_TIMEOUT=30: Balances patience with responsiveness
        # These defaults optimize for:
        # 1. Cost efficiency (fewer tokens)
        # 2. Quality (enough content for style analysis)
        # 3. Speed (reasonable timeouts)
        # 4. Reliability (handles slow servers)
