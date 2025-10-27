"""Tests for research client using Perplexity Sonar via OpenRouter."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.research_client import ResearchClient
from src.models import StyleHints, ResearchResult
from src.config import Configuration


@pytest.fixture
def mock_config():
    """Provide mock configuration."""
    return Configuration(
        api_key="test_key",
        model="openai/gpt-4o-mini",
        research_enabled=True,
        research_model="perplexity/sonar-pro",
    )


@pytest.fixture
def sample_style_hints():
    """Provide sample style hints for testing."""
    return StyleHints(
        content_depth="descriptive",
        technical_level="mixed",
        preferred_sources="academic",
        focus_areas=["data visualization", "statistics"],
    )


class TestResearchClient:
    """Test ResearchClient class."""

    def test_init_with_config(self, mock_config):
        """Test research client initialization with configuration."""
        client = ResearchClient(mock_config)
        assert client.config == mock_config

    def test_research_returns_research_result(
        self, mock_config, sample_style_hints
    ):
        """Test that research returns ResearchResult instance."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = """
            # Research on AI Development

            ## Key Facts and Statistics
            - AI market size: $150B in 2023
            - 75% of enterprises use AI

            ## Expert Quotes and Sources
            - "AI is transforming software" - John Smith, MIT
            - Study from Stanford shows productivity gains

            ## Full Research
            Comprehensive analysis of AI development...
            """
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)
            result = client.research("AI Development", sample_style_hints)

            assert isinstance(result, ResearchResult)
            assert result.topic == "AI Development"
            assert isinstance(result.facts_and_stats, list)
            assert isinstance(result.quotes_and_sources, list)
            assert isinstance(result.full_research_text, str)
            assert isinstance(result.timestamp, datetime)

    def test_research_uses_research_model(self, mock_config, sample_style_hints):
        """Test that research uses the configured research model."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = "# Research\n\nBasic research text"
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)
            client.research("Test Topic", sample_style_hints)

            # Verify generate was called with research_model override
            mock_llm.generate.assert_called_once()
            call_kwargs = mock_llm.generate.call_args[1]
            assert "model" in call_kwargs
            assert call_kwargs["model"] == mock_config.research_model

    def test_research_loads_prompt_template(self, mock_config, sample_style_hints):
        """Test that research loads the research prompt template."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            with patch("src.research_client.PromptManager") as mock_pm_class:
                mock_llm = Mock()
                mock_llm.generate.return_value = "# Research"
                mock_llm_class.return_value = mock_llm

                mock_pm = Mock()
                mock_pm.load_prompt.return_value = "Research {topic}"
                mock_pm_class.return_value = mock_pm

                client = ResearchClient(mock_config)
                client.research("Test", sample_style_hints)

                # Verify research prompt was loaded
                mock_pm.load_prompt.assert_called_once()
                call_args = mock_pm.load_prompt.call_args[0]
                assert "research" in call_args[0]

    def test_research_includes_style_hints_in_prompt(
        self, mock_config, sample_style_hints
    ):
        """Test that style hints are included in research prompt."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            with patch("src.research_client.PromptManager") as mock_pm_class:
                mock_llm = Mock()
                mock_llm.generate.return_value = "# Research"
                mock_llm_class.return_value = mock_llm

                mock_pm = Mock()
                mock_pm.load_prompt.return_value = (
                    "Research {topic} with depth {content_depth}"
                )
                mock_pm_class.return_value = mock_pm

                client = ResearchClient(mock_config)
                client.research("AI", sample_style_hints)

                # Verify generate was called with prompt containing hints
                mock_llm.generate.assert_called_once()
                call_args = mock_llm.generate.call_args[0][0]
                assert "descriptive" in call_args  # content_depth
                assert "AI" in call_args  # topic

    def test_research_parses_facts_section(self, mock_config, sample_style_hints):
        """Test that research correctly parses facts and statistics."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = """
            # Research

            ## Key Facts and Statistics
            - Fact 1: AI market is $150B
            - Fact 2: 75% adoption rate
            - Fact 3: Growth of 30% YoY

            ## Other Section
            Content here
            """
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)
            result = client.research("AI", sample_style_hints)

            assert len(result.facts_and_stats) == 3
            assert "AI market is $150B" in result.facts_and_stats[0]
            assert "75% adoption rate" in result.facts_and_stats[1]
            assert "30% YoY" in result.facts_and_stats[2]

    def test_research_parses_quotes_section(self, mock_config, sample_style_hints):
        """Test that research correctly parses quotes and sources."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = """
            # Research

            ## Expert Quotes and Sources
            - "AI is the future" - John Doe, MIT
            - "Innovation accelerates" - Jane Smith, Stanford
            - Study from Harvard shows 50% improvement

            ## Other Section
            """
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)
            result = client.research("AI", sample_style_hints)

            assert len(result.quotes_and_sources) == 3
            # Each should be a dict with 'text' key
            assert isinstance(result.quotes_and_sources[0], dict)
            assert "text" in result.quotes_and_sources[0]

    def test_research_includes_full_text(self, mock_config, sample_style_hints):
        """Test that full research text is captured."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            research_text = """
            # AI Development Research

            ## Key Facts
            - Fact 1

            ## Quotes
            - Quote 1

            ## Full Analysis
            This is comprehensive research with multiple paragraphs
            discussing various aspects of AI development.
            """
            mock_llm.generate.return_value = research_text
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)
            result = client.research("AI", sample_style_hints)

            assert result.full_research_text == research_text.strip()
            assert "comprehensive research" in result.full_research_text

    def test_research_handles_malformed_response(
        self, mock_config, sample_style_hints
    ):
        """Test graceful handling of malformed research response."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            # Response without expected sections
            mock_llm.generate.return_value = "Just some text without structure"
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)
            result = client.research("AI", sample_style_hints)

            # Should still return valid ResearchResult with empty lists
            assert isinstance(result, ResearchResult)
            assert result.facts_and_stats == []
            assert result.quotes_and_sources == []
            assert result.full_research_text != ""

    def test_research_handles_empty_sections(self, mock_config, sample_style_hints):
        """Test handling of sections with no items."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = """
            # Research

            ## Key Facts and Statistics

            ## Expert Quotes and Sources

            Some content but no bullet points.
            """
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)
            result = client.research("AI", sample_style_hints)

            assert result.facts_and_stats == []
            assert result.quotes_and_sources == []

    def test_research_counts_sources(self, mock_config, sample_style_hints):
        """Test that sources_count is calculated correctly."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = """
            ## Expert Quotes and Sources
            - Quote 1 - Source A
            - Quote 2 - Source B
            - Quote 3 - Source C
            """
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)
            result = client.research("AI", sample_style_hints)

            # sources_count should be based on quotes
            assert result.sources_count == 3

    def test_research_handles_api_error(self, mock_config, sample_style_hints):
        """Test handling of API errors during research."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.side_effect = Exception("API Error")
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)

            # Should raise exception (not swallow it)
            with pytest.raises(Exception, match="API Error"):
                client.research("AI", sample_style_hints)

    def test_research_timestamp_is_recent(self, mock_config, sample_style_hints):
        """Test that research timestamp is set to current time."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = "# Research"
            mock_llm_class.return_value = mock_llm

            before = datetime.now()
            client = ResearchClient(mock_config)
            result = client.research("AI", sample_style_hints)
            after = datetime.now()

            # Timestamp should be between before and after
            assert before <= result.timestamp <= after

    def test_research_preserves_topic(self, mock_config, sample_style_hints):
        """Test that research result preserves original topic."""
        with patch("src.research_client.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate.return_value = "# Research"
            mock_llm_class.return_value = mock_llm

            client = ResearchClient(mock_config)
            result = client.research("Original Topic Name", sample_style_hints)

            assert result.topic == "Original Topic Name"
