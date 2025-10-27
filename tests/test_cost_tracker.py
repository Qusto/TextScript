"""Tests for CostTracker."""

import pytest
from src.cost_tracker import CostTracker
from src.models import GenerationCost, ArticleCostReport
from src.llm_client import LLMClient


class TestCostTracker:
    """Test CostTracker class for tracking API costs."""

    def test_cost_tracker_initialization(self):
        """Test creating CostTracker instance."""
        client = LLMClient(api_key="test_key")
        tracker = CostTracker(client)

        assert tracker is not None
        assert tracker.llm_client == client
        assert len(tracker.generation_ids) == 0

    def test_track_generation_id(self, mocker):
        """Test tracking generation ID from API response."""
        # Mock OpenAI client response with generation_id
        mock_completion = mocker.Mock()
        mock_completion.id = "gen-abc123"
        mock_completion.choices = [
            mocker.Mock(message=mocker.Mock(content="Test content"))
        ]

        mock_client = mocker.Mock()
        mock_client.chat.completions.create.return_value = mock_completion
        mocker.patch("src.llm_client.OpenAI", return_value=mock_client)

        client = LLMClient(api_key="test_key")
        tracker = CostTracker(client)

        # Track an analyze_style call
        result = tracker.analyze_style("Sample content")

        assert result == "Test content"
        assert len(tracker.generation_ids) == 1
        assert tracker.generation_ids[0] == ("gen-abc123", "style_analysis")

    def test_track_multiple_calls(self, mocker):
        """Test tracking multiple API calls."""
        # Mock OpenAI client
        mock_completion_1 = mocker.Mock()
        mock_completion_1.id = "gen-style-123"
        mock_completion_1.choices = [
            mocker.Mock(message=mocker.Mock(content="Style result"))
        ]

        mock_completion_2 = mocker.Mock()
        mock_completion_2.id = "gen-article-456"
        mock_completion_2.choices = [
            mocker.Mock(message=mocker.Mock(content="Article result"))
        ]

        mock_client = mocker.Mock()
        mock_client.chat.completions.create.side_effect = [
            mock_completion_1,
            mock_completion_2,
        ]
        mocker.patch("src.llm_client.OpenAI", return_value=mock_client)

        client = LLMClient(api_key="test_key")
        tracker = CostTracker(client)

        # Track multiple calls
        tracker.analyze_style("Content")
        tracker.generate_article("Topic", "Style")

        assert len(tracker.generation_ids) == 2
        assert tracker.generation_ids[0] == ("gen-style-123", "style_analysis")
        assert tracker.generation_ids[1] == ("gen-article-456", "article_generation")

    def test_fetch_generation_cost(self, mocker):
        """Test fetching cost from OpenRouter /generation endpoint."""
        client = LLMClient(api_key="test_key")
        tracker = CostTracker(client)

        # Mock requests.get for /generation endpoint
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "data": {
                "model": "anthropic/claude-3.5-sonnet",
                "native_tokens_prompt": 150,
                "native_tokens_completion": 350,
                "total_cost": 0.0123,
            }
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        # Fetch cost
        cost = tracker._fetch_generation_cost("gen-abc123", "test_stage")

        assert cost.generation_id == "gen-abc123"
        assert cost.stage == "test_stage"
        assert cost.model == "anthropic/claude-3.5-sonnet"
        assert cost.prompt_tokens == 150
        assert cost.completion_tokens == 350
        assert cost.total_tokens == 500
        assert cost.cost_usd == 0.0123

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://openrouter.ai/api/v1/generation" in call_args[0][0]
        assert "gen-abc123" in call_args[0][0]

    def test_fetch_generation_cost_with_error(self, mocker):
        """Test handling errors when fetching cost data."""
        client = LLMClient(api_key="test_key")
        tracker = CostTracker(client)

        # Mock requests.get to raise exception
        mock_get = mocker.patch("requests.get", side_effect=Exception("API Error"))

        # Fetch cost should return None on error
        cost = tracker._fetch_generation_cost("gen-abc123", "test_stage")

        assert cost is None

    def test_get_cost_report(self, mocker):
        """Test generating cost report."""
        # Mock OpenAI client
        mock_completion = mocker.Mock()
        mock_completion.id = "gen-123"
        mock_completion.choices = [
            mocker.Mock(message=mocker.Mock(content="Result"))
        ]

        mock_client = mocker.Mock()
        mock_client.chat.completions.create.return_value = mock_completion
        mocker.patch("src.llm_client.OpenAI", return_value=mock_client)

        # Mock /generation endpoint
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "data": {
                "model": "openai/gpt-4o-mini",
                "native_tokens_prompt": 100,
                "native_tokens_completion": 200,
                "total_cost": 0.0050,
            }
        }
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch("requests.get", return_value=mock_response)

        client = LLMClient(api_key="test_key")
        tracker = CostTracker(client)

        # Track a call
        tracker.analyze_style("Content")

        # Get cost report
        report = tracker.get_cost_report()

        assert isinstance(report, ArticleCostReport)
        assert len(report.costs) == 1
        assert report.total_cost_usd == 0.0050
        assert report.total_tokens == 300

    def test_get_cost_report_empty(self):
        """Test cost report with no tracked calls."""
        client = LLMClient(api_key="test_key")
        tracker = CostTracker(client)

        report = tracker.get_cost_report()

        assert isinstance(report, ArticleCostReport)
        assert len(report.costs) == 0
        assert report.total_cost_usd == 0.0
        assert report.total_tokens == 0

    def test_get_cost_report_with_failures(self, mocker):
        """Test cost report when some cost fetches fail."""
        # Mock OpenAI client
        mock_completion_1 = mocker.Mock()
        mock_completion_1.id = "gen-success"
        mock_completion_1.choices = [
            mocker.Mock(message=mocker.Mock(content="Result 1"))
        ]

        mock_completion_2 = mocker.Mock()
        mock_completion_2.id = "gen-fail"
        mock_completion_2.choices = [
            mocker.Mock(message=mocker.Mock(content="Result 2"))
        ]

        mock_client = mocker.Mock()
        mock_client.chat.completions.create.side_effect = [
            mock_completion_1,
            mock_completion_2,
        ]
        mocker.patch("src.llm_client.OpenAI", return_value=mock_client)

        # Mock /generation endpoint - first succeeds, second fails
        def mock_get_side_effect(url, *args, **kwargs):
            if "gen-success" in url:
                mock_resp = mocker.Mock()
                mock_resp.json.return_value = {
                    "data": {
                        "model": "openai/gpt-4o-mini",
                        "native_tokens_prompt": 100,
                        "native_tokens_completion": 200,
                        "total_cost": 0.0050,
                    }
                }
                mock_resp.raise_for_status = mocker.Mock()
                return mock_resp
            else:
                raise Exception("API Error")

        mocker.patch("requests.get", side_effect=mock_get_side_effect)

        client = LLMClient(api_key="test_key")
        tracker = CostTracker(client)

        # Track two calls
        tracker.analyze_style("Content 1")
        tracker.generate_article("Topic", "Style")

        # Get cost report - should only include successful fetch
        report = tracker.get_cost_report()

        assert len(report.costs) == 1
        assert report.costs[0].generation_id == "gen-success"
        assert report.total_cost_usd == 0.0050


class TestArticleCostReport:
    """Test ArticleCostReport class."""

    def test_empty_report(self):
        """Test empty cost report."""
        report = ArticleCostReport()

        assert len(report.costs) == 0
        assert report.total_cost_usd == 0.0
        assert report.total_tokens == 0

    def test_report_with_costs(self):
        """Test cost report with multiple costs."""
        costs = [
            GenerationCost(
                model="openai/gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
                cost_usd=0.0050,
                generation_id="gen-1",
                stage="style_analysis",
            ),
            GenerationCost(
                model="anthropic/claude-3.5-sonnet",
                prompt_tokens=150,
                completion_tokens=250,
                total_tokens=400,
                cost_usd=0.0120,
                generation_id="gen-2",
                stage="article_generation",
            ),
        ]

        report = ArticleCostReport(costs=costs)

        assert len(report.costs) == 2
        assert report.total_cost_usd == 0.0170
        assert report.total_tokens == 700

    def test_print_report(self, mocker, capsys):
        """Test printing cost report to console."""
        # Mock logger to capture output (imported inside print_report)
        mock_logger = mocker.patch("loguru.logger")

        costs = [
            GenerationCost(
                model="openai/gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
                cost_usd=0.0050,
                generation_id="gen-1",
                stage="style_analysis",
            ),
        ]

        report = ArticleCostReport(costs=costs)
        report.print_report()

        # Verify logger was called with cost information
        assert mock_logger.info.called
        assert mock_logger.success.called

        # Check that formatted strings contain expected values
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        success_calls = [str(call) for call in mock_logger.success.call_args_list]

        combined_output = " ".join(info_calls + success_calls)
        assert "style_analysis" in combined_output
        assert "$0.01" in combined_output  # $0.0050 rounds to $0.01
        assert "300" in combined_output  # tokens
