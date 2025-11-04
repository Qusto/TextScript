# Test for enhanced colorful logging in EvaluationRunner
# Tests formatting helpers and log output structure

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from loguru import logger
import sys
from io import StringIO

from src.evaluator.runner import EvaluationRunner
from src.evaluator.config import EvalConfig
from src.evaluator.metrics.numeric import CosineSimilarityResult, BERTScoreResult
from src.evaluator.metrics.judge import JudgeResult


@pytest.fixture(autouse=True)
def capture_loguru(monkeypatch):
    """Capture Loguru logs for testing."""
    # Create a StringIO to capture logs
    log_buffer = StringIO()

    # Remove default handlers and add test handler
    logger.remove()
    handler_id = logger.add(log_buffer, format="{message}", colorize=False)

    yield log_buffer

    # Cleanup
    logger.remove(handler_id)


@pytest.fixture
def mock_config():
    """Create mock EvalConfig for testing."""
    config = Mock(spec=EvalConfig)
    config.dataset_path = "./test_dataset"
    config.output_path = "./test_output"
    config.metrics_numeric = {"cosine_similarity": True, "bert_score": True}
    config.metrics_judge = {"content_judge": True, "style_judge": True}
    return config


@pytest.fixture
def runner(mock_config):
    """Create EvaluationRunner with mocked dependencies."""
    adapter = Mock()
    numeric_metrics = Mock()
    judge_evaluator = Mock()

    runner = EvaluationRunner(
        config=mock_config,
        adapter=adapter,
        numeric_metrics=numeric_metrics,
        judge_evaluator=judge_evaluator
    )
    return runner


class TestFormattingHelpers:
    """Test helper functions for formatting output."""

    def test_format_size_kilobytes(self, runner):
        """Test _format_size returns KB for small texts."""
        # 50KB = 51,200 chars
        result = runner._format_size(51200)
        assert result == "50KB"

    def test_format_size_megabytes(self, runner):
        """Test _format_size returns MB for large texts."""
        # 1.5MB = 1,572,864 chars
        result = runner._format_size(1572864)
        assert result == "1.5MB"

    def test_format_size_small(self, runner):
        """Test _format_size handles small texts."""
        result = runner._format_size(500)
        assert result == "0KB"

    def test_get_text_stats(self, runner):
        """Test _get_text_stats returns formatted statistics."""
        text = "a" * 51200  # 50KB
        result = runner._get_text_stats(text)
        assert "50KB" in result
        assert "51,200 chars" in result


class TestLogStage:
    """Test stage logging with colors and icons."""

    def test_log_stage_format(self, runner, capture_loguru):
        """Test _log_stage outputs correct format with markup."""
        runner._log_stage(1, 4, "📦", "Loading test case")

        # Get captured log output
        log_output = capture_loguru.getvalue()

        # Check log message contains expected elements
        assert "[1/4]" in log_output
        assert "📦" in log_output
        assert "Loading test case" in log_output
        # Note: <cyan> tags are removed by colorize=False in test fixture


class TestEvaluateCaseLogging:
    """Test logging structure in _evaluate_case method."""

    def test_case_logging_stages(self, runner, capture_loguru, tmp_path):
        """Test that all 4 stages are logged with correct icons."""
        # Setup mocks
        case_path = tmp_path / "author" / "case_001"
        case_path.mkdir(parents=True)

        # Create test files
        (case_path / "source_texts.txt").write_text("source text" * 1000)
        (case_path / "ground_truth_article.txt").write_text("ground truth" * 1000)
        (case_path / "topic.json").write_text('{"topic": "Test", "theses": []}')

        output_path = tmp_path / "output"

        # Mock adapter
        runner.adapter.generate_article = Mock(return_value="generated text" * 1000)

        # Mock metrics with proper types
        from datetime import datetime
        mock_cosine = CosineSimilarityResult(
            score=0.856,
            model="test-model",
            computed_at=datetime.now().isoformat()
        )
        mock_bert = BERTScoreResult(
            precision=0.900,
            recall=0.925,
            f1=0.912,
            model="test-bert",
            computed_at=datetime.now().isoformat()
        )

        runner.numeric_metrics.compute_cosine_similarity = Mock(return_value=mock_cosine)
        runner.numeric_metrics.compute_bert_score = Mock(return_value=mock_bert)

        mock_content = JudgeResult(
            score=4,
            reasoning="Test reasoning with enough characters to pass validation requirements.",
            model="test-judge",
            prompt_version="v1.0",
            computed_at=datetime.now().isoformat()
        )
        mock_style = JudgeResult(
            score=4,
            reasoning="Test reasoning with enough characters to pass validation requirements.",
            model="test-judge",
            prompt_version="v1.0",
            computed_at=datetime.now().isoformat()
        )

        runner.judge_evaluator.evaluate_content = Mock(return_value=mock_content)
        runner.judge_evaluator.evaluate_style = Mock(return_value=mock_style)

        # Run evaluation
        result = runner._evaluate_case(case_path, output_path, perfect_test=False)

        # Get captured log output
        log_output = capture_loguru.getvalue()

        # Check all stages are present
        assert "[1/4]" in log_output and "📦" in log_output, "Stage 1 missing"
        assert "[2/4]" in log_output and "⚙️" in log_output, "Stage 2 missing"
        assert "[3/4]" in log_output and "📊" in log_output, "Stage 3 missing"
        assert "[4/4]" in log_output and "💾" in log_output, "Stage 4 missing"

    def test_input_summary_logged(self, runner, capture_loguru, tmp_path):
        """Test that input summary is logged."""
        case_path = tmp_path / "author" / "case_001"
        case_path.mkdir(parents=True)

        (case_path / "source_texts.txt").write_text("a" * 51200)  # 50KB
        (case_path / "ground_truth_article.txt").write_text("b" * 20480)  # 20KB
        (case_path / "topic.json").write_text('{"topic": "Test Topic", "theses": []}')

        output_path = tmp_path / "output"
        runner.adapter.generate_article = Mock(return_value="generated")

        runner._evaluate_case(case_path, output_path, perfect_test=False)

        # Get captured log output
        log_output = capture_loguru.getvalue()

        # Check input summary is present
        assert "Input:" in log_output, "Input summary not logged"
        assert "50KB" in log_output, "Source size not logged"
        assert "20KB" in log_output, "Ground truth size not logged"
        assert "Test Topic" in log_output, "Topic not logged"

    def test_results_summary_logged(self, runner, capture_loguru, tmp_path):
        """Test that final results summary is logged."""
        case_path = tmp_path / "author" / "case_001"
        case_path.mkdir(parents=True)

        (case_path / "source_texts.txt").write_text("source")
        (case_path / "ground_truth_article.txt").write_text("ground truth")
        (case_path / "topic.json").write_text('{"topic": "Test", "theses": []}')

        output_path = tmp_path / "output"
        runner.adapter.generate_article = Mock(return_value="generated")

        # Mock metrics with known values using proper types
        from datetime import datetime
        mock_cosine = CosineSimilarityResult(
            score=0.856,
            model="test-model",
            computed_at=datetime.now().isoformat()
        )
        mock_bert = BERTScoreResult(
            precision=0.900,
            recall=0.925,
            f1=0.912,
            model="test-bert",
            computed_at=datetime.now().isoformat()
        )

        runner.numeric_metrics.compute_cosine_similarity = Mock(return_value=mock_cosine)
        runner.numeric_metrics.compute_bert_score = Mock(return_value=mock_bert)

        mock_content = JudgeResult(
            score=4,
            reasoning="Test reasoning with enough characters to pass validation requirements.",
            model="test-judge",
            prompt_version="v1.0",
            computed_at=datetime.now().isoformat()
        )
        mock_style = JudgeResult(
            score=5,
            reasoning="Test reasoning with enough characters to pass validation requirements.",
            model="test-judge",
            prompt_version="v1.0",
            computed_at=datetime.now().isoformat()
        )

        runner.judge_evaluator.evaluate_content = Mock(return_value=mock_content)
        runner.judge_evaluator.evaluate_style = Mock(return_value=mock_style)

        runner._evaluate_case(case_path, output_path, perfect_test=False)

        # Get captured log output
        log_output = capture_loguru.getvalue()

        # Check results summary is present
        assert "Results:" in log_output, "Results summary not logged"
        assert "cosine=0.856" in log_output, "Cosine metric not in results"
        assert "bert_f1=0.912" in log_output, "BERTScore not in results"
        assert "content=4/5" in log_output, "Content score not in results"
        assert "style=5/5" in log_output, "Style score not in results"
        assert "✅" in log_output, "Checkmark emoji missing"


class TestPerfectTestMode:
    """Test logging in perfect test mode."""

    def test_perfect_test_stage_marker(self, runner, capture_loguru, tmp_path):
        """Test that perfect test mode shows correct stage 2 message."""
        case_path = tmp_path / "author" / "case_001"
        case_path.mkdir(parents=True)

        (case_path / "source_texts.txt").write_text("source")
        ground_truth = "ground truth text" * 100
        (case_path / "ground_truth_article.txt").write_text(ground_truth)
        (case_path / "topic.json").write_text('{"topic": "Test", "theses": []}')

        output_path = tmp_path / "output"

        runner._evaluate_case(case_path, output_path, perfect_test=True)

        # Get captured log output
        log_output = capture_loguru.getvalue()

        # Check stage 2 message mentions source texts (author baseline)
        assert "[2/4]" in log_output, "Stage 2 not logged"
        assert "source" in log_output.lower(), "Source texts not mentioned"
