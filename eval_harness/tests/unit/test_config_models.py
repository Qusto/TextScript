# AICODE-NOTE: Unit tests for configuration models (T019-T023)
# AICODE-NOTE: Tests Pydantic validation for DatasetConfig, EvalConfig, and result models

"""Unit tests for configuration Pydantic models"""

import pytest
from datetime import datetime

from src.dataset_builder.config import DatasetConfig, TopicData
from src.evaluator.config import (
    EvalConfig,
    CosineSimilarityResult,
    BERTScoreResult,
    NumericMetrics,
    JudgeResult
)


class TestTopicData:
    """Test TopicData Pydantic model (T020)"""

    def test_valid_topic_data(self):
        """Test TopicData with valid data.

        AICODE-NOTE: Tests T020 - basic validation
        """
        data = TopicData(
            topic="Test topic",
            theses=["one", "two", "three", "four", "five"]
        )

        assert data.topic == "Test topic"
        assert len(data.theses) == 5

    def test_topic_too_long(self):
        """Test TopicData rejects topic > 100 chars.

        AICODE-NOTE: Tests T020 - max 100 char topic validation
        """
        with pytest.raises(ValueError):
            TopicData(
                topic="a" * 101,
                theses=["one", "two", "three", "four", "five"]
            )

    def test_too_few_theses(self):
        """Test TopicData rejects < 5 theses.

        AICODE-NOTE: Tests T020 - minimum 5 theses validation
        """
        with pytest.raises(ValueError):
            TopicData(
                topic="Test",
                theses=["one", "two", "three", "four"]
            )

    def test_too_many_theses(self):
        """Test TopicData rejects > 10 theses.

        AICODE-NOTE: Tests T020 - maximum 10 theses validation
        """
        with pytest.raises(ValueError):
            TopicData(
                topic="Test",
                theses=["one", "two", "three", "four", "five",
                       "six", "seven", "eight", "nine", "ten", "eleven"]
            )

    def test_thesis_too_long(self):
        """Test TopicData rejects thesis > 500 chars.

        AICODE-NOTE: Tests T020 - max 500 char per thesis validation
        """
        with pytest.raises(ValueError, match="too long"):
            TopicData(
                topic="Test",
                theses=["a" * 501, "two", "three", "four", "five"]
            )


class TestDatasetConfig:
    """Test DatasetConfig Pydantic model (T019)"""

    def test_valid_config(self):
        """Test DatasetConfig with valid values.

        AICODE-NOTE: Tests T019 - basic validation
        """
        config = DatasetConfig(
            corpus_path="./corpus",
            output_path="./dataset",
            min_texts_per_author=10,
            m_style_texts=5,
            k_test_cases=5,
            neutralizer_model_id="openai/gpt-4o",
            max_tokens_for_neutralizer=4000
        )

        assert config.min_texts_per_author == 10
        assert config.m_style_texts == 5
        assert config.k_test_cases == 5

    def test_text_allocation_validation(self):
        """Test m_style_texts + k_test_cases <= min_texts_per_author.

        AICODE-NOTE: Tests T019 - critical constraint validation
        """
        with pytest.raises(ValueError, match="Text allocation invalid"):
            DatasetConfig(
                corpus_path="./corpus",
                output_path="./dataset",
                min_texts_per_author=10,
                m_style_texts=6,  # 6 + 5 = 11 > 10
                k_test_cases=5,
                neutralizer_model_id="openai/gpt-4o",
                max_tokens_for_neutralizer=4000
            )

    def test_min_texts_too_low(self):
        """Test min_texts_per_author must be >= 5.

        AICODE-NOTE: Tests T019 - minimum text count validation
        """
        with pytest.raises(ValueError):
            DatasetConfig(
                corpus_path="./corpus",
                output_path="./dataset",
                min_texts_per_author=4,  # Too low
                m_style_texts=2,
                k_test_cases=2,
                neutralizer_model_id="openai/gpt-4o",
                max_tokens_for_neutralizer=4000
            )


class TestEvalConfig:
    """Test EvalConfig Pydantic model (T022)"""

    def test_valid_config(self):
        """Test EvalConfig with valid values.

        AICODE-NOTE: Tests T022 - basic validation
        """
        config = EvalConfig(
            dataset_path="./dataset",
            output_path="./results",
            generation_model_id="openai/gpt-4o",
            judge_model_id="openai/gpt-4o",
            metrics_numeric={"cosine_similarity": True, "bert_score": True},
            metrics_judge={"content_judge": True, "style_judge": True}
        )

        assert config.llm_timeout == 120  # Default
        assert config.max_retries == 3  # Default

    def test_at_least_one_metric_required(self):
        """Test EvalConfig requires at least one metric enabled.

        AICODE-NOTE: Tests T022 - at least one metric validation
        """
        with pytest.raises(ValueError, match="At least one metric must be enabled"):
            EvalConfig(
                dataset_path="./dataset",
                output_path="./results",
                generation_model_id="openai/gpt-4o",
                judge_model_id="openai/gpt-4o",
                metrics_numeric={"cosine_similarity": False, "bert_score": False},
                metrics_judge={"content_judge": False, "style_judge": False}
            )


class TestNumericMetrics:
    """Test NumericMetrics and related models (T023)"""

    def test_cosine_similarity_valid(self):
        """Test CosineSimilarityResult with valid score.

        AICODE-NOTE: Tests T023 - score bounds [0.0-1.0]
        """
        result = CosineSimilarityResult(
            score=0.85,
            model="all-MiniLM-L6-v2",
            computed_at=datetime.now()
        )

        assert 0.0 <= result.score <= 1.0

    def test_cosine_similarity_out_of_bounds(self):
        """Test CosineSimilarityResult rejects invalid scores.

        AICODE-NOTE: Tests T023 - score validation
        """
        with pytest.raises(ValueError):
            CosineSimilarityResult(
                score=1.5,  # Out of bounds
                model="test",
                computed_at=datetime.now()
            )

    def test_bert_score_valid(self):
        """Test BERTScoreResult with valid scores.

        AICODE-NOTE: Tests T023 - all scores in [0.0-1.0]
        """
        result = BERTScoreResult(
            precision=0.88,
            recall=0.86,
            f1=0.87,
            model="bert-base-uncased",
            computed_at=datetime.now()
        )

        assert 0.0 <= result.precision <= 1.0
        assert 0.0 <= result.recall <= 1.0
        assert 0.0 <= result.f1 <= 1.0


class TestJudgeResult:
    """Test JudgeResult model (T023)"""

    def test_valid_judge_result(self):
        """Test JudgeResult with valid data.

        AICODE-NOTE: Tests T023 - score bounds [1-5], reasoning length
        """
        result = JudgeResult(
            score=4,
            reasoning="This is a good explanation with at least fifty characters to meet minimum.",
            model="openai/gpt-4o",
            prompt_version="v1",
            computed_at=datetime.now()
        )

        assert 1 <= result.score <= 5
        assert 50 <= len(result.reasoning) <= 500

    def test_score_out_of_bounds(self):
        """Test JudgeResult rejects invalid scores.

        AICODE-NOTE: Tests T023 - score validation [1-5]
        """
        with pytest.raises(ValueError):
            JudgeResult(
                score=6,  # Out of bounds
                reasoning="a" * 60,
                model="test",
                prompt_version="v1",
                computed_at=datetime.now()
            )

    def test_reasoning_too_short(self):
        """Test JudgeResult rejects reasoning < 50 chars.

        AICODE-NOTE: Tests T023 - minimum reasoning length
        """
        with pytest.raises(ValueError):
            JudgeResult(
                score=4,
                reasoning="Too short",  # < 50 chars
                model="test",
                prompt_version="v1",
                computed_at=datetime.now()
            )

    def test_reasoning_too_long(self):
        """Test JudgeResult rejects reasoning > 500 chars.

        AICODE-NOTE: Tests T023 - maximum reasoning length
        """
        with pytest.raises(ValueError):
            JudgeResult(
                score=4,
                reasoning="a" * 501,  # > 500 chars
                model="test",
                prompt_version="v1",
                computed_at=datetime.now()
            )
