# AICODE-NOTE: T058 - Unit tests for Ugly Script integration adapter
# AICODE-NOTE: Tests article generation invocation with source texts and topic
# AICODE-NOTE: Tests error handling for API failures and timeouts
# AICODE-NOTE: UglyScriptAdapter adapts existing generator for evaluation use

"""Unit tests for Ugly Script integration (article generation)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestUglyScriptAdapter:
    """Test UglyScriptAdapter for article generation.

    AICODE-NOTE: T061-T065 - Tests adapter that calls Ugly Script functions
    AICODE-NOTE: Adapter wraps src.llm_client analyze_style() and generate_article()
    """

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for testing."""
        return Mock()

    @pytest.fixture
    def sample_data(self):
        """Sample test case data."""
        return {
            "source_texts": "Mark Twain wrote with humor and wit. His sentences were short and punchy. The Mississippi River featured prominently in his works.",
            "topic": "Adventures on the Mississippi River",
            "theses": [
                "Story takes place on Mississippi River",
                "Main character is young boy",
                "Adventures involve friendship and exploration",
                "Time period is 19th century America"
            ],
            "generation_model_id": "meta-llama/llama-3-8b-instruct"
        }

    def test_adapter_initialization(self, mock_llm_client, sample_data):
        """Test UglyScriptAdapter initialization with model config.

        AICODE-NOTE: T062 - Tests __init__() with model configuration
        """
        from src.evaluator.integration import UglyScriptAdapter

        adapter = UglyScriptAdapter(
            llm_client=mock_llm_client,
            generation_model_id=sample_data["generation_model_id"]
        )

        assert adapter.generation_model_id == sample_data["generation_model_id"]
        assert adapter.llm_client == mock_llm_client

    @patch('src.evaluator.integration.CostTracker')
    def test_generate_article_calls_analyze_style(
        self,
        mock_cost_tracker_class,
        mock_llm_client,
        sample_data
    ):
        """Test generate_article() calls analyze_style() with source texts.

        AICODE-NOTE: T063 - Tests analyze_style() invocation
        AICODE-NOTE: Ugly Script requires style analysis before generation
        """
        from src.evaluator.integration import UglyScriptAdapter

        # Mock CostTracker methods
        mock_cost_tracker = Mock()
        mock_cost_tracker.analyze_style.return_value = "Style profile: humorous, concise, vivid"
        mock_cost_tracker.generate_article.return_value = "Generated article text here."
        mock_cost_tracker_class.return_value = mock_cost_tracker

        adapter = UglyScriptAdapter(
            llm_client=mock_llm_client,
            generation_model_id=sample_data["generation_model_id"]
        )

        result = adapter.generate_article(
            source_texts=sample_data["source_texts"],
            topic_data={
                "topic": sample_data["topic"],
                "theses": sample_data["theses"]
            }
        )

        # Verify analyze_style was called
        mock_cost_tracker.analyze_style.assert_called_once_with(
            sample_data["source_texts"]
        )

        # Verify result
        assert result == "Generated article text here."

    @patch('src.evaluator.integration.CostTracker')
    def test_generate_article_calls_generate_with_topic(
        self,
        mock_cost_tracker_class,
        mock_llm_client,
        sample_data
    ):
        """Test generate_article() calls generation with topic and theses.

        AICODE-NOTE: T063 - Tests generate_article() invocation
        AICODE-NOTE: Topic and theses are formatted into content prompt
        """
        from src.evaluator.integration import UglyScriptAdapter

        mock_cost_tracker = Mock()
        mock_cost_tracker.analyze_style.return_value = "Style: humorous"
        mock_cost_tracker.generate_article.return_value = "Article about adventures"
        mock_cost_tracker_class.return_value = mock_cost_tracker

        adapter = UglyScriptAdapter(
            llm_client=mock_llm_client,
            generation_model_id=sample_data["generation_model_id"]
        )

        result = adapter.generate_article(
            source_texts=sample_data["source_texts"],
            topic_data={
                "topic": sample_data["topic"],
                "theses": sample_data["theses"]
            }
        )

        # Verify generate_article was called with formatted topic
        mock_cost_tracker.generate_article.assert_called_once()
        call_args = mock_cost_tracker.generate_article.call_args

        # Topic argument should include topic and theses
        topic_arg = call_args[0][0]  # First positional argument
        assert sample_data["topic"] in topic_arg
        # Check that theses are included
        for thesis in sample_data["theses"]:
            assert thesis in topic_arg

    @patch('src.evaluator.integration.CostTracker')
    def test_generate_article_handles_api_timeout(
        self,
        mock_cost_tracker_class,
        mock_llm_client,
        sample_data
    ):
        """Test error handling for API timeout during generation.

        AICODE-NOTE: T064 - Tests timeout error handling
        """
        from src.evaluator.integration import UglyScriptAdapter

        mock_cost_tracker = Mock()
        mock_cost_tracker.analyze_style.side_effect = TimeoutError("API timeout")
        mock_cost_tracker_class.return_value = mock_cost_tracker

        adapter = UglyScriptAdapter(
            llm_client=mock_llm_client,
            generation_model_id=sample_data["generation_model_id"]
        )

        # Should raise with context about which step failed
        with pytest.raises(RuntimeError, match="style analysis.*timeout"):
            adapter.generate_article(
                source_texts=sample_data["source_texts"],
                topic_data={
                    "topic": sample_data["topic"],
                    "theses": sample_data["theses"]
                }
            )

    @patch('src.evaluator.integration.CostTracker')
    def test_generate_article_handles_api_failure(
        self,
        mock_cost_tracker_class,
        mock_llm_client,
        sample_data
    ):
        """Test error handling for API failures during generation.

        AICODE-NOTE: T064 - Tests API error handling with context
        """
        from src.evaluator.integration import UglyScriptAdapter

        mock_cost_tracker = Mock()
        mock_cost_tracker.analyze_style.return_value = "Style profile"
        mock_cost_tracker.generate_article.side_effect = RuntimeError("API key invalid")
        mock_cost_tracker_class.return_value = mock_cost_tracker

        adapter = UglyScriptAdapter(
            llm_client=mock_llm_client,
            generation_model_id=sample_data["generation_model_id"]
        )

        # Should wrap exception with context
        with pytest.raises(RuntimeError, match="article generation.*API key"):
            adapter.generate_article(
                source_texts=sample_data["source_texts"],
                topic_data={
                    "topic": sample_data["topic"],
                    "theses": sample_data["theses"]
                }
            )

    @patch('src.evaluator.integration.CostTracker')
    def test_generate_article_with_progress_callback(
        self,
        mock_cost_tracker_class,
        mock_llm_client,
        sample_data
    ):
        """Test progress callback support for long-running operations.

        AICODE-NOTE: T065 - Tests optional callback for progress tracking
        """
        from src.evaluator.integration import UglyScriptAdapter

        mock_cost_tracker = Mock()
        mock_cost_tracker.analyze_style.return_value = "Style profile"
        mock_cost_tracker.generate_article.return_value = "Generated article"
        mock_cost_tracker_class.return_value = mock_cost_tracker

        adapter = UglyScriptAdapter(
            llm_client=mock_llm_client,
            generation_model_id=sample_data["generation_model_id"]
        )

        # Mock progress callback
        progress_callback = Mock()

        result = adapter.generate_article(
            source_texts=sample_data["source_texts"],
            topic_data={
                "topic": sample_data["topic"],
                "theses": sample_data["theses"]
            },
            progress_callback=progress_callback
        )

        # Verify callback was called at key stages
        assert progress_callback.call_count >= 2  # At least: analyzing style, generating article
        call_messages = [call[0][0] for call in progress_callback.call_args_list]

        # Check callback messages
        assert any("style" in msg.lower() for msg in call_messages)
        assert any("generat" in msg.lower() for msg in call_messages)

    @patch('src.evaluator.integration.CostTracker')
    def test_generate_article_returns_text(
        self,
        mock_cost_tracker_class,
        mock_llm_client,
        sample_data
    ):
        """Test generate_article() returns generated text string."""
        from src.evaluator.integration import UglyScriptAdapter

        mock_cost_tracker = Mock()
        mock_cost_tracker.analyze_style.return_value = "Style profile"
        mock_cost_tracker.generate_article.return_value = "This is the generated article content with sufficient length."
        mock_cost_tracker_class.return_value = mock_cost_tracker

        adapter = UglyScriptAdapter(
            llm_client=mock_llm_client,
            generation_model_id=sample_data["generation_model_id"]
        )

        result = adapter.generate_article(
            source_texts=sample_data["source_texts"],
            topic_data={
                "topic": sample_data["topic"],
                "theses": sample_data["theses"]
            }
        )

        # Verify return type
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_article_validates_inputs(self, mock_llm_client, sample_data):
        """Test input validation for source_texts and topic_data."""
        from src.evaluator.integration import UglyScriptAdapter

        adapter = UglyScriptAdapter(
            llm_client=mock_llm_client,
            generation_model_id=sample_data["generation_model_id"]
        )

        # Empty source texts
        with pytest.raises(ValueError, match="source_texts.*empty"):
            adapter.generate_article(
                source_texts="",
                topic_data={
                    "topic": sample_data["topic"],
                    "theses": sample_data["theses"]
                }
            )

        # Invalid topic_data (missing topic)
        with pytest.raises(ValueError, match="topic_data.*topic"):
            adapter.generate_article(
                source_texts=sample_data["source_texts"],
                topic_data={"theses": sample_data["theses"]}
            )

        # Invalid topic_data (missing theses)
        with pytest.raises(ValueError, match="topic_data.*theses"):
            adapter.generate_article(
                source_texts=sample_data["source_texts"],
                topic_data={"topic": sample_data["topic"]}
            )
