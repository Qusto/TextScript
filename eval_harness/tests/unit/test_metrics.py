# AICODE-NOTE: T056 - Unit tests for numeric metrics computation
# AICODE-NOTE: Tests cosine similarity and BERTScore calculation
# AICODE-NOTE: Uses mocked models for deterministic testing

"""Unit tests for metrics computation (cosine similarity and BERTScore)."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from eval_harness.src.evaluator.config import (
    CosineSimilarityResult,
    BERTScoreResult,
    NumericMetrics
)


class TestCosineSimilarityResult:
    """Test CosineSimilarityResult validation."""

    def test_valid_score(self):
        """Test creating result with valid score."""
        result = CosineSimilarityResult(
            score=0.85,
            model="all-MiniLM-L6-v2",
            computed_at=datetime.now()
        )
        assert result.score == 0.85
        assert result.model == "all-MiniLM-L6-v2"

    def test_score_bounds_validation(self):
        """Test score must be in [0.0, 1.0] range."""
        # Valid bounds
        CosineSimilarityResult(score=0.0, model="test", computed_at=datetime.now())
        CosineSimilarityResult(score=1.0, model="test", computed_at=datetime.now())

        # Invalid bounds
        with pytest.raises(ValueError, match="greater than or equal to 0.0"):
            CosineSimilarityResult(score=-0.1, model="test", computed_at=datetime.now())

        with pytest.raises(ValueError, match="less than or equal to 1.0"):
            CosineSimilarityResult(score=1.5, model="test", computed_at=datetime.now())


class TestBERTScoreResult:
    """Test BERTScoreResult validation."""

    def test_valid_scores(self):
        """Test creating result with valid precision/recall/F1."""
        result = BERTScoreResult(
            precision=0.88,
            recall=0.86,
            f1=0.87,
            model="bert-base-uncased",
            computed_at=datetime.now()
        )
        assert result.precision == 0.88
        assert result.recall == 0.86
        assert result.f1 == 0.87

    def test_all_scores_bounded(self):
        """Test all scores must be in [0.0, 1.0] range."""
        # Invalid precision
        with pytest.raises(ValueError):
            BERTScoreResult(
                precision=-0.1,
                recall=0.8,
                f1=0.8,
                model="test",
                computed_at=datetime.now()
            )

        # Invalid recall
        with pytest.raises(ValueError):
            BERTScoreResult(
                precision=0.8,
                recall=1.5,
                f1=0.8,
                model="test",
                computed_at=datetime.now()
            )

        # Invalid F1
        with pytest.raises(ValueError):
            BERTScoreResult(
                precision=0.8,
                recall=0.8,
                f1=2.0,
                model="test",
                computed_at=datetime.now()
            )


class TestNumericMetricsComputation:
    """Test numeric metrics computation with NumericMetrics class.

    AICODE-NOTE: This will test the actual computation logic
    AICODE-NOTE: We'll implement NumericMetrics class in metrics/numeric.py
    """

    @pytest.fixture
    def sample_texts(self):
        """Sample texts for testing."""
        return {
            "generated": "The cat sat on the mat. It was a sunny day.",
            "ground_truth": "The cat was sitting on the mat. The weather was sunny.",
            "empty": "",
            "very_short": "Hi."
        }

    @patch('sentence_transformers.SentenceTransformer')
    def test_cosine_similarity_computation(self, mock_model_class, sample_texts):
        """Test cosine similarity computation with mocked embeddings.

        AICODE-NOTE: Mocking sentence-transformers to avoid model download
        AICODE-NOTE: Tests the computation logic, not the actual model
        """
        # AICODE-NOTE: Import will be available after we implement the module
        from eval_harness.src.evaluator.metrics.numeric import NumericMetrics

        # Mock the embedding model
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        # AICODE-NOTE: Create embeddings with known cosine similarity
        # Two vectors with cosine similarity = 0.85 (approximately)
        embedding1 = np.array([[1.0, 0.5, 0.3]])
        embedding2 = np.array([[0.9, 0.6, 0.2]])

        mock_model.encode.side_effect = [embedding1, embedding2]

        # Compute metric
        metrics = NumericMetrics(embedding_model="all-MiniLM-L6-v2")
        result = metrics.compute_cosine_similarity(
            sample_texts["generated"],
            sample_texts["ground_truth"]
        )

        # Validate result
        assert isinstance(result, CosineSimilarityResult)
        assert 0.0 <= result.score <= 1.0
        assert result.model == "all-MiniLM-L6-v2"
        assert isinstance(result.computed_at, datetime)

    @patch('sentence_transformers.SentenceTransformer')
    def test_cosine_similarity_identical_texts(self, mock_model_class):
        """Test cosine similarity of identical texts should be ~1.0."""
        from eval_harness.src.evaluator.metrics.numeric import NumericMetrics

        mock_model = Mock()
        mock_model_class.return_value = mock_model

        # Same embedding for identical texts
        embedding = np.array([[1.0, 0.5, 0.3]])
        mock_model.encode.side_effect = [embedding, embedding]

        metrics = NumericMetrics(embedding_model="all-MiniLM-L6-v2")
        result = metrics.compute_cosine_similarity("Same text", "Same text")

        # Cosine similarity of identical vectors should be 1.0
        assert result.score >= 0.99

    @patch('sentence_transformers.SentenceTransformer')
    def test_cosine_similarity_empty_text(self, mock_model_class, sample_texts):
        """Test cosine similarity with empty text returns None."""
        from eval_harness.src.evaluator.metrics.numeric import NumericMetrics

        mock_model = Mock()
        mock_model_class.return_value = mock_model

        metrics = NumericMetrics(embedding_model="all-MiniLM-L6-v2")

        # Empty generated text
        result = metrics.compute_cosine_similarity(
            sample_texts["empty"],
            sample_texts["ground_truth"]
        )
        assert result is None

        # Empty ground truth
        result = metrics.compute_cosine_similarity(
            sample_texts["generated"],
            sample_texts["empty"]
        )
        assert result is None

    @patch('bert_score.score')
    def test_bert_score_computation(self, mock_bert_score, sample_texts):
        """Test BERTScore computation with mocked bert_score library.

        AICODE-NOTE: Mocking bert_score to avoid model download
        AICODE-NOTE: bert_score.score returns (precision, recall, f1) tensors
        """
        from eval_harness.src.evaluator.metrics.numeric import NumericMetrics

        # AICODE-NOTE: Mock bert_score.score return value
        # Returns PyTorch tensors with single values
        import torch
        mock_bert_score.return_value = (
            torch.tensor([0.88]),  # precision
            torch.tensor([0.86]),  # recall
            torch.tensor([0.87])   # f1
        )

        metrics = NumericMetrics()
        result = metrics.compute_bert_score(
            sample_texts["generated"],
            sample_texts["ground_truth"]
        )

        # Validate result
        assert isinstance(result, BERTScoreResult)
        assert result.precision == pytest.approx(0.88, abs=0.01)
        assert result.recall == pytest.approx(0.86, abs=0.01)
        assert result.f1 == pytest.approx(0.87, abs=0.01)
        assert result.model == "bert-base-uncased"
        assert isinstance(result.computed_at, datetime)

    @patch('bert_score.score')
    def test_bert_score_empty_text(self, mock_bert_score, sample_texts):
        """Test BERTScore with empty text returns None."""
        from eval_harness.src.evaluator.metrics.numeric import NumericMetrics

        metrics = NumericMetrics()

        # Empty texts should return None without calling bert_score
        result = metrics.compute_bert_score(
            sample_texts["empty"],
            sample_texts["ground_truth"]
        )
        assert result is None
        mock_bert_score.assert_not_called()

    @patch('bert_score.score')
    def test_bert_score_handles_exceptions(self, mock_bert_score, sample_texts):
        """Test BERTScore handles computation errors gracefully."""
        from eval_harness.src.evaluator.metrics.numeric import NumericMetrics

        # Simulate bert_score failure
        mock_bert_score.side_effect = RuntimeError("Out of memory")

        metrics = NumericMetrics()
        result = metrics.compute_bert_score(
            sample_texts["generated"],
            sample_texts["ground_truth"]
        )

        # Should return None on error, not raise
        assert result is None


class TestNumericMetricsModel:
    """Test NumericMetrics Pydantic model."""

    def test_optional_metrics(self):
        """Test that both metrics are optional."""
        # No metrics
        metrics = NumericMetrics()
        assert metrics.cosine_similarity is None
        assert metrics.bert_score is None

        # Only cosine
        metrics = NumericMetrics(
            cosine_similarity=CosineSimilarityResult(
                score=0.85,
                model="test",
                computed_at=datetime.now()
            )
        )
        assert metrics.cosine_similarity is not None
        assert metrics.bert_score is None

    def test_json_serialization(self):
        """Test metrics can be serialized to JSON."""
        metrics = NumericMetrics(
            cosine_similarity=CosineSimilarityResult(
                score=0.85,
                model="all-MiniLM-L6-v2",
                computed_at=datetime.now()
            ),
            bert_score=BERTScoreResult(
                precision=0.88,
                recall=0.86,
                f1=0.87,
                model="bert-base-uncased",
                computed_at=datetime.now()
            )
        )

        # Should serialize without errors
        json_data = metrics.model_dump_json()
        assert "cosine_similarity" in json_data
        assert "bert_score" in json_data
