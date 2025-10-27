"""Tests for style hints extraction from style profiles."""

import pytest
from unittest.mock import Mock, patch

from src.style_hints_extractor import StyleHintsExtractor
from src.models import StyleProfile, StyleHints
from src.config import Configuration


@pytest.fixture
def mock_config():
    """Provide mock configuration."""
    return Configuration(
        api_key="test_key",
        model="openai/gpt-4o-mini",
        research_model="perplexity/sonar-pro",
    )


@pytest.fixture
def sample_style_profile():
    """Provide sample style profile for testing."""
    return StyleProfile(
        profile_text="""
        This author uses descriptive, flowing language with rich metaphors.
        The writing style is technical but accessible, balancing jargon with clear explanations.
        The author prefers academic sources and in-depth analysis.
        Key focus areas: data visualization, statistical methods, and practical examples.
        """,
        source_urls=["https://example.com/article1"],
        url_hash="abc123",
    )


class TestStyleHintsExtractor:
    """Test StyleHintsExtractor class."""

    def test_init_with_config(self, mock_config):
        """Test extractor initialization with configuration."""
        extractor = StyleHintsExtractor(mock_config)
        assert extractor.config == mock_config

    def test_extract_returns_style_hints(self, mock_config, sample_style_profile):
        """Test that extract returns StyleHints instance."""
        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = """
            {
                "content_depth": "descriptive",
                "technical_level": "mixed",
                "preferred_sources": "academic",
                "focus_areas": ["data visualization", "statistics"]
            }
            """
            mock_llm_class.return_value = mock_llm

            extractor = StyleHintsExtractor(mock_config)
            hints = extractor.extract(sample_style_profile)

            assert isinstance(hints, StyleHints)
            assert hints.content_depth in ["descriptive", "concrete", "balanced"]
            assert hints.technical_level in ["technical", "simple", "mixed"]
            assert hints.preferred_sources in ["academic", "practical", "varied"]
            assert isinstance(hints.focus_areas, list)

    def test_extract_uses_correct_model(self, mock_config, sample_style_profile):
        """Test that extractor uses the configured model."""
        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = '{"content_depth": "balanced"}'
            mock_llm_class.return_value = mock_llm

            extractor = StyleHintsExtractor(mock_config)
            extractor.extract(sample_style_profile)

            # Verify LLMClient was created with correct parameters
            mock_llm_class.assert_called_once_with(
                api_key=mock_config.api_key, model=mock_config.model
            )

    def test_extract_loads_prompt_template(self, mock_config, sample_style_profile):
        """Test that extract loads the style hints prompt template."""
        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            with patch("src.style_hints_extractor.PromptManager") as mock_pm_class:
                mock_llm = Mock()
                mock_llm.generate.return_value = '{"content_depth": "balanced"}'
                mock_llm_class.return_value = mock_llm

                mock_pm = Mock()
                mock_pm.load_prompt.return_value = "Test prompt {profile_text}"
                mock_pm_class.return_value = mock_pm

                extractor = StyleHintsExtractor(mock_config)
                extractor.extract(sample_style_profile)

                # Verify prompt was loaded
                mock_pm.load_prompt.assert_called_once()
                call_args = mock_pm.load_prompt.call_args[0]
                assert "research_style_hints" in call_args[0]

    def test_extract_handles_json_response(self, mock_config, sample_style_profile):
        """Test that extract correctly parses JSON response."""
        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = """
            {
                "content_depth": "concrete",
                "technical_level": "technical",
                "preferred_sources": "practical",
                "focus_areas": ["examples", "case studies", "tutorials"]
            }
            """
            mock_llm_class.return_value = mock_llm

            extractor = StyleHintsExtractor(mock_config)
            hints = extractor.extract(sample_style_profile)

            assert hints.content_depth == "concrete"
            assert hints.technical_level == "technical"
            assert hints.preferred_sources == "practical"
            assert "examples" in hints.focus_areas
            assert "case studies" in hints.focus_areas

    def test_extract_handles_malformed_json(self, mock_config, sample_style_profile):
        """Test graceful handling of malformed JSON response."""
        extractor = StyleHintsExtractor(mock_config)

        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = "Not valid JSON at all"
            mock_llm_class.return_value = mock_llm

            # Should return default StyleHints on parse error
            hints = extractor.extract(sample_style_profile)

            assert isinstance(hints, StyleHints)
            assert hints.content_depth == "balanced"  # default
            assert hints.technical_level == "mixed"  # default

    def test_extract_handles_partial_json(self, mock_config, sample_style_profile):
        """Test handling of JSON with missing fields."""
        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            # Only some fields present
            mock_llm.generate.return_value = """
            {
                "content_depth": "descriptive"
            }
            """
            mock_llm_class.return_value = mock_llm

            extractor = StyleHintsExtractor(mock_config)
            hints = extractor.extract(sample_style_profile)

            assert hints.content_depth == "descriptive"
            # Other fields should have defaults
            assert hints.technical_level == "mixed"
            assert hints.preferred_sources == "varied"

    def test_extract_validates_literal_values(self, mock_config, sample_style_profile):
        """Test that invalid literal values fall back to defaults."""
        extractor = StyleHintsExtractor(mock_config)

        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            # Invalid values that don't match Literal types
            mock_llm.generate.return_value = """
            {
                "content_depth": "super_descriptive",
                "technical_level": "genius_level",
                "preferred_sources": "wikipedia"
            }
            """
            mock_llm_class.return_value = mock_llm

            hints = extractor.extract(sample_style_profile)

            # Should fall back to defaults for invalid values
            assert hints.content_depth in ["descriptive", "concrete", "balanced"]
            assert hints.technical_level in ["technical", "simple", "mixed"]
            assert hints.preferred_sources in ["academic", "practical", "varied"]

    def test_extract_includes_profile_in_prompt(self, mock_config, sample_style_profile):
        """Test that style profile text is included in prompt."""
        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            with patch("src.style_hints_extractor.PromptManager") as mock_pm_class:
                mock_llm = Mock()
                mock_llm.generate.return_value = '{"content_depth": "balanced"}'
                mock_llm_class.return_value = mock_llm

                mock_pm = Mock()
                mock_pm.load_prompt.return_value = "Analyze: {profile_text}"
                mock_pm_class.return_value = mock_pm

                extractor = StyleHintsExtractor(mock_config)
                extractor.extract(sample_style_profile)

                # Verify generate was called with prompt containing profile text
                mock_llm.generate.assert_called_once()
                call_args = mock_llm.generate.call_args[0][0]
                assert sample_style_profile.profile_text in call_args

    def test_extract_handles_empty_focus_areas(self, mock_config, sample_style_profile):
        """Test handling of empty focus_areas list."""
        extractor = StyleHintsExtractor(mock_config)

        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = """
            {
                "content_depth": "balanced",
                "focus_areas": []
            }
            """
            mock_llm_class.return_value = mock_llm

            hints = extractor.extract(sample_style_profile)

            # Should use default focus_areas if empty
            assert len(hints.focus_areas) > 0
            assert hints.focus_areas == ["data", "examples"]

    def test_extract_cleans_focus_areas(self, mock_config, sample_style_profile):
        """Test that focus_areas are cleaned and normalized."""
        extractor = StyleHintsExtractor(mock_config)

        with patch("src.style_hints_extractor.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = """
            {
                "focus_areas": ["  Data Analysis  ", "MACHINE LEARNING", "statistics"]
            }
            """
            mock_llm_class.return_value = mock_llm

            hints = extractor.extract(sample_style_profile)

            # Focus areas should be cleaned (stripped, lowercased)
            assert all(area == area.strip().lower() for area in hints.focus_areas)
