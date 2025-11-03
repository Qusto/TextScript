# AICODE-NOTE: T059 - Integration test for single case evaluation
# AICODE-NOTE: Tests full pipeline: load case → generate → compute metrics → save
# AICODE-NOTE: Uses real file I/O and mock LLM calls

"""Integration tests for single test case evaluation pipeline."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime


class TestSingleCaseEvaluation:
    """Test complete evaluation pipeline for a single test case.

    AICODE-NOTE: T082 - Tests EvaluationRunner._evaluate_case() method
    AICODE-NOTE: Integration test verifies all components work together
    """

    @pytest.fixture
    def test_case_dir(self, tmp_path):
        """Create a temporary test case directory with required files."""
        case_dir = tmp_path / "mark_twain" / "case_001"
        case_dir.mkdir(parents=True)

        # Create source_texts.txt
        source_texts = "Mark Twain wrote with humor. His sentences were short and punchy."
        (case_dir / "source_texts.txt").write_text(source_texts, encoding="utf-8")

        # Create ground_truth_article.txt
        ground_truth = "The Mississippi River flows through America. Mark Twain loved the river deeply."
        (case_dir / "ground_truth_article.txt").write_text(ground_truth, encoding="utf-8")

        # Create topic.json
        topic_data = {
            "topic": "The Mississippi River in American Literature",
            "theses": [
                "Mississippi River is central to American identity",
                "The river represents freedom and adventure",
                "River commerce shaped regional culture"
            ]
        }
        (case_dir / "topic.json").write_text(json.dumps(topic_data, indent=2), encoding="utf-8")

        return case_dir

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create output directory for evaluation results."""
        output = tmp_path / "eval_results" / "20250103_120000" / "mark_twain" / "case_001"
        output.mkdir(parents=True)
        return output

    @pytest.fixture
    def mock_config(self):
        """Mock EvalConfig for testing."""
        from eval_harness.src.evaluator.config import EvalConfig

        return EvalConfig(
            dataset_path="./eval_dataset/",
            output_path="./eval_results/",
            generation_model_id="meta-llama/llama-3-8b-instruct",
            judge_model_id="openai/gpt-4o",
            metrics_numeric={
                "cosine_similarity": True,
                "bert_score": True
            },
            metrics_judge={
                "content_judge": True,
                "style_judge": True
            },
            embedding_model="all-MiniLM-L6-v2",
            llm_timeout=120,
            max_retries=3
        )

    @patch('eval_harness.src.evaluator.integration.UglyScriptAdapter')
    @patch('eval_harness.src.evaluator.metrics.numeric.NumericMetrics')
    @patch('eval_harness.src.evaluator.metrics.judge.JudgeEvaluator')
    def test_evaluate_case_full_pipeline(
        self,
        mock_judge_class,
        mock_numeric_class,
        mock_adapter_class,
        test_case_dir,
        output_dir,
        mock_config
    ):
        """Test complete evaluation pipeline for single case.

        AICODE-NOTE: Tests load → generate → compute metrics → save
        """
        from eval_harness.src.evaluator.runner import EvaluationRunner
        from eval_harness.src.evaluator.config import (
            CosineSimilarityResult,
            BERTScoreResult,
            JudgeResult
        )

        # Mock adapter (article generation)
        mock_adapter = Mock()
        mock_adapter.generate_article.return_value = "Generated article about Mississippi River adventures and Mark Twain's connection to it."
        mock_adapter_class.return_value = mock_adapter

        # Mock numeric metrics
        mock_numeric = Mock()
        mock_numeric.compute_cosine_similarity.return_value = CosineSimilarityResult(
            score=0.85,
            model="all-MiniLM-L6-v2",
            computed_at=datetime.now()
        )
        mock_numeric.compute_bert_score.return_value = BERTScoreResult(
            precision=0.88,
            recall=0.86,
            f1=0.87,
            model="bert-base-uncased",
            computed_at=datetime.now()
        )
        mock_numeric_class.return_value = mock_numeric

        # Mock judge evaluator
        mock_judge = Mock()
        mock_judge.evaluate_content.return_value = JudgeResult(
            score=4,
            reasoning="Generated article covers most key ideas with strong accuracy. Minor details differ but main concepts are present.",
            model="openai/gpt-4o",
            prompt_version="content_judge_v1",
            computed_at=datetime.now()
        )
        mock_judge.evaluate_style.return_value = JudgeResult(
            score=3,
            reasoning="Style shows moderate similarity with some matching patterns. Sentence structure differs from reference style.",
            model="openai/gpt-4o",
            prompt_version="style_judge_v1",
            computed_at=datetime.now()
        )
        mock_judge_class.return_value = mock_judge

        # Create runner and evaluate case
        runner = EvaluationRunner(
            config=mock_config,
            adapter=mock_adapter,
            numeric_metrics=mock_numeric,
            judge_evaluator=mock_judge
        )

        # Evaluate case
        result = runner._evaluate_case(
            case_path=test_case_dir,
            output_path=output_dir
        )

        # Verify adapter was called with correct inputs
        mock_adapter.generate_article.assert_called_once()
        call_args = mock_adapter.generate_article.call_args
        assert "humor" in call_args[1]["source_texts"]
        assert call_args[1]["topic_data"]["topic"] == "The Mississippi River in American Literature"

        # Verify metrics were computed
        mock_numeric.compute_cosine_similarity.assert_called_once()
        mock_numeric.compute_bert_score.assert_called_once()
        mock_judge.evaluate_content.assert_called_once()
        mock_judge.evaluate_style.assert_called_once()

        # Verify result structure
        assert result is not None
        assert "generated_article" in result
        assert "numeric_metrics" in result
        assert "content_judge" in result
        assert "style_judge" in result

    @patch('eval_harness.src.evaluator.integration.UglyScriptAdapter')
    def test_evaluate_case_saves_generated_article(
        self,
        mock_adapter_class,
        test_case_dir,
        output_dir,
        mock_config
    ):
        """Test that generated article is saved to generated_article.txt.

        AICODE-NOTE: T084 - Tests _save_case_results() file writing
        """
        from eval_harness.src.evaluator.runner import EvaluationRunner

        mock_adapter = Mock()
        generated_text = "This is the generated article text that should be saved to file."
        mock_adapter.generate_article.return_value = generated_text
        mock_adapter_class.return_value = mock_adapter

        runner = EvaluationRunner(
            config=mock_config,
            adapter=mock_adapter,
            numeric_metrics=None,  # Disabled for this test
            judge_evaluator=None   # Disabled for this test
        )

        runner._evaluate_case(
            case_path=test_case_dir,
            output_path=output_dir
        )

        # Verify generated article file exists
        generated_file = output_dir / "generated_article.txt"
        assert generated_file.exists()

        # Verify content
        saved_text = generated_file.read_text(encoding="utf-8")
        assert saved_text == generated_text

    @patch('eval_harness.src.evaluator.metrics.numeric.NumericMetrics')
    def test_evaluate_case_saves_numeric_metrics(
        self,
        mock_numeric_class,
        test_case_dir,
        output_dir,
        mock_config
    ):
        """Test that numeric metrics are saved to metrics_numeric.json.

        AICODE-NOTE: T084 - Tests JSON serialization and file writing
        """
        from eval_harness.src.evaluator.runner import EvaluationRunner
        from eval_harness.src.evaluator.config import CosineSimilarityResult, BERTScoreResult

        mock_numeric = Mock()
        mock_numeric.compute_cosine_similarity.return_value = CosineSimilarityResult(
            score=0.85,
            model="all-MiniLM-L6-v2",
            computed_at=datetime.now()
        )
        mock_numeric.compute_bert_score.return_value = BERTScoreResult(
            precision=0.88,
            recall=0.86,
            f1=0.87,
            model="bert-base-uncased",
            computed_at=datetime.now()
        )
        mock_numeric_class.return_value = mock_numeric

        runner = EvaluationRunner(
            config=mock_config,
            adapter=Mock(),  # Not testing generation here
            numeric_metrics=mock_numeric,
            judge_evaluator=None
        )

        runner._evaluate_case(
            case_path=test_case_dir,
            output_path=output_dir
        )

        # Verify metrics file exists
        metrics_file = output_dir / "metrics_numeric.json"
        assert metrics_file.exists()

        # Verify content
        with open(metrics_file) as f:
            data = json.load(f)

        assert "cosine_similarity" in data
        assert data["cosine_similarity"]["score"] == 0.85
        assert "bert_score" in data
        assert data["bert_score"]["f1"] == 0.87

    def test_evaluate_case_handles_generation_failure(
        self,
        test_case_dir,
        output_dir,
        mock_config
    ):
        """Test error recovery when article generation fails.

        AICODE-NOTE: T086 - Tests error recovery to continue evaluation
        """
        from eval_harness.src.evaluator.runner import EvaluationRunner

        mock_adapter = Mock()
        mock_adapter.generate_article.side_effect = RuntimeError("API timeout")

        runner = EvaluationRunner(
            config=mock_config,
            adapter=mock_adapter,
            numeric_metrics=None,
            judge_evaluator=None
        )

        # Should not raise exception, but return None or partial result
        result = runner._evaluate_case(
            case_path=test_case_dir,
            output_path=output_dir
        )

        # Result should indicate failure
        assert result is None or "error" in result

    @patch('eval_harness.src.evaluator.metrics.numeric.NumericMetrics')
    def test_evaluate_case_continues_on_metric_failure(
        self,
        mock_numeric_class,
        test_case_dir,
        output_dir,
        mock_config
    ):
        """Test that single metric failure doesn't stop entire evaluation.

        AICODE-NOTE: T086 - Tests graceful degradation when metrics fail
        """
        from eval_harness.src.evaluator.runner import EvaluationRunner
        from eval_harness.src.evaluator.config import CosineSimilarityResult

        mock_numeric = Mock()
        # Cosine works, BERTScore fails
        mock_numeric.compute_cosine_similarity.return_value = CosineSimilarityResult(
            score=0.85,
            model="all-MiniLM-L6-v2",
            computed_at=datetime.now()
        )
        mock_numeric.compute_bert_score.side_effect = RuntimeError("Out of memory")
        mock_numeric_class.return_value = mock_numeric

        runner = EvaluationRunner(
            config=mock_config,
            adapter=Mock(generate_article=Mock(return_value="Article text")),
            numeric_metrics=mock_numeric,
            judge_evaluator=None
        )

        # Should complete despite BERTScore failure
        result = runner._evaluate_case(
            case_path=test_case_dir,
            output_path=output_dir
        )

        # Result should include successful metrics
        assert result is not None
        assert "numeric_metrics" in result
        # Cosine should be present, BERTScore should be None
        assert result["numeric_metrics"]["cosine_similarity"] is not None
        assert result["numeric_metrics"]["bert_score"] is None


class TestLoadTestCase:
    """Test loading test case files from dataset.

    AICODE-NOTE: T081 - Tests EvaluationRunner._load_test_case()
    """

    def test_load_test_case_all_files(self, tmp_path):
        """Test loading all required files from test case directory."""
        from eval_harness.src.evaluator.runner import EvaluationRunner

        # Create test case directory
        case_dir = tmp_path / "mark_twain" / "case_001"
        case_dir.mkdir(parents=True)

        source_texts = "Source text content here"
        ground_truth = "Ground truth article content"
        topic_data = {"topic": "Test Topic", "theses": ["Thesis 1", "Thesis 2"]}

        (case_dir / "source_texts.txt").write_text(source_texts, encoding="utf-8")
        (case_dir / "ground_truth_article.txt").write_text(ground_truth, encoding="utf-8")
        (case_dir / "topic.json").write_text(json.dumps(topic_data), encoding="utf-8")

        # Load test case
        runner = EvaluationRunner(
            config=Mock(),
            adapter=Mock(),
            numeric_metrics=None,
            judge_evaluator=None
        )

        result = runner._load_test_case(case_dir)

        # Verify all data loaded
        assert result["source_texts"] == source_texts
        assert result["ground_truth_article"] == ground_truth
        assert result["topic_data"]["topic"] == "Test Topic"
        assert len(result["topic_data"]["theses"]) == 2

    def test_load_test_case_missing_file(self, tmp_path):
        """Test error handling when required file is missing."""
        from eval_harness.src.evaluator.runner import EvaluationRunner

        case_dir = tmp_path / "author" / "case_001"
        case_dir.mkdir(parents=True)

        # Only create some files, not all
        (case_dir / "source_texts.txt").write_text("Source", encoding="utf-8")
        # Missing: ground_truth_article.txt and topic.json

        runner = EvaluationRunner(
            config=Mock(),
            adapter=Mock(),
            numeric_metrics=None,
            judge_evaluator=None
        )

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError, match="ground_truth_article.txt"):
            runner._load_test_case(case_dir)
