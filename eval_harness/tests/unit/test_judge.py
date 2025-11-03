# AICODE-NOTE: T057 - Unit tests for LLM-as-Judge evaluation
# AICODE-NOTE: Tests content and style prompt construction
# AICODE-NOTE: Tests score parsing from JSON responses
# AICODE-NOTE: Tests retry logic for malformed responses

"""Unit tests for LLM-as-Judge evaluation (content and style judges)."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import json

from src.evaluator.config import JudgeResult


class TestJudgeResultValidation:
    """Test JudgeResult Pydantic model validation."""

    def test_valid_score_range(self):
        """Test score must be integer in [1, 5] range."""
        # Valid scores
        for score in [1, 2, 3, 4, 5]:
            result = JudgeResult(
                score=score,
                reasoning="This is a test reasoning with at least fifty characters to pass validation.",
                model="openai/gpt-4o",
                prompt_version="content_judge_v1",
                computed_at=datetime.now()
            )
            assert result.score == score

    def test_invalid_score_bounds(self):
        """Test score outside [1, 5] range raises error."""
        # Score too low
        with pytest.raises(ValueError, match="greater than or equal to 1"):
            JudgeResult(
                score=0,
                reasoning="Valid reasoning with enough characters to pass validation test.",
                model="test",
                prompt_version="v1",
                computed_at=datetime.now()
            )

        # Score too high
        with pytest.raises(ValueError, match="less than or equal to 5"):
            JudgeResult(
                score=6,
                reasoning="Valid reasoning with enough characters to pass validation test.",
                model="test",
                prompt_version="v1",
                computed_at=datetime.now()
            )

    def test_reasoning_length_validation(self):
        """Test reasoning must be 50-500 characters."""
        # Too short (< 50 chars)
        with pytest.raises(ValueError, match="at least 50 characters"):
            JudgeResult(
                score=3,
                reasoning="Too short",
                model="test",
                prompt_version="v1",
                computed_at=datetime.now()
            )

        # Valid minimum length
        JudgeResult(
            score=3,
            reasoning="x" * 50,  # Exactly 50 characters
            model="test",
            prompt_version="v1",
            computed_at=datetime.now()
        )

        # Valid maximum length
        JudgeResult(
            score=3,
            reasoning="x" * 500,  # Exactly 500 characters
            model="test",
            prompt_version="v1",
            computed_at=datetime.now()
        )

        # Too long (> 500 chars)
        with pytest.raises(ValueError, match="at most 500 characters"):
            JudgeResult(
                score=3,
                reasoning="x" * 501,
                model="test",
                prompt_version="v1",
                computed_at=datetime.now()
            )


class TestContentJudgeEvaluator:
    """Test content judge evaluation logic.

    AICODE-NOTE: Tests JudgeEvaluator.evaluate_content() method
    AICODE-NOTE: Validates prompt construction and score parsing
    """

    @pytest.fixture
    def sample_texts(self):
        """Sample texts for testing."""
        return {
            "generated": "The cat sat on the mat. It was a warm, sunny afternoon in June.",
            "ground_truth": "A feline rested upon a rug. The day was pleasantly warm and bright.",
        }

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for testing."""
        return Mock()

    def test_content_judge_prompt_construction(self, mock_llm_client, sample_texts):
        """Test content judge prompt includes correct texts and instructions.

        AICODE-NOTE: Will be implemented in metrics/judge.py
        """
        from src.evaluator.metrics.judge import JudgeEvaluator

        # Mock LLM response
        mock_llm_client.generate.return_value = json.dumps({
            "score": 4,
            "reasoning": "TEXT_A covers most key ideas from TEXT_B with strong content accuracy. Minor details differ but main concepts present."
        })

        evaluator = JudgeEvaluator(
            llm_client=mock_llm_client,
            judge_model_id="openai/gpt-4o"
        )

        result = evaluator.evaluate_content(
            generated_article=sample_texts["generated"],
            ground_truth_article=sample_texts["ground_truth"]
        )

        # Verify LLM was called with correct format
        assert mock_llm_client.generate.called
        call_args = mock_llm_client.generate.call_args

        # Check model_id
        assert call_args[1]["model_id"] == "openai/gpt-4o"

        # Check messages structure
        messages = call_args[1]["messages"]
        assert len(messages) == 2  # System + User
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        # Check content judge instructions in user message
        user_content = messages[1]["content"]
        assert "TEXT_A" in user_content
        assert "TEXT_B" in user_content
        assert sample_texts["generated"] in user_content
        assert sample_texts["ground_truth"] in user_content
        assert "completeness and accuracy of content" in user_content.lower()

    def test_content_judge_score_parsing(self, mock_llm_client, sample_texts):
        """Test parsing valid JSON response from content judge."""
        from src.evaluator.metrics.judge import JudgeEvaluator

        # Mock valid JSON response
        mock_llm_client.generate.return_value = json.dumps({
            "score": 4,
            "reasoning": "Generated article covers the topic well with most key ideas present. Some minor details are missing but overall strong content coverage."
        })

        evaluator = JudgeEvaluator(
            llm_client=mock_llm_client,
            judge_model_id="openai/gpt-4o"
        )

        result = evaluator.evaluate_content(
            generated_article=sample_texts["generated"],
            ground_truth_article=sample_texts["ground_truth"]
        )

        # Validate result
        assert isinstance(result, JudgeResult)
        assert result.score == 4
        assert len(result.reasoning) >= 50
        assert result.model == "openai/gpt-4o"
        assert result.prompt_version == "content_judge_v1"

    def test_content_judge_handles_markdown_json(self, mock_llm_client, sample_texts):
        """Test parsing JSON wrapped in markdown code blocks.

        AICODE-NOTE: Claude often returns ```json ... ``` format
        """
        from src.evaluator.metrics.judge import JudgeEvaluator

        # Mock response with markdown code block
        mock_llm_client.generate.return_value = """```json
{
    "score": 3,
    "reasoning": "The generated article attempts to cover the topic but has notable gaps in content. Some key ideas are missing or incorrectly presented."
}
```"""

        evaluator = JudgeEvaluator(
            llm_client=mock_llm_client,
            judge_model_id="anthropic/claude-3-5-sonnet"
        )

        result = evaluator.evaluate_content(
            generated_article=sample_texts["generated"],
            ground_truth_article=sample_texts["ground_truth"]
        )

        # Should successfully parse despite markdown wrapper
        assert result.score == 3
        assert "notable gaps" in result.reasoning

    def test_content_judge_retry_on_malformed_response(self, mock_llm_client, sample_texts):
        """Test retry logic when LLM returns malformed JSON.

        AICODE-NOTE: Max 2 retries with format reminder in prompt
        """
        from src.evaluator.metrics.judge import JudgeEvaluator

        # First call: invalid JSON
        # Second call: missing score field
        # Third call: valid response
        mock_llm_client.generate.side_effect = [
            "This is not JSON at all",
            json.dumps({"reasoning": "Missing score field but has valid reasoning text here for testing purposes."}),
            json.dumps({
                "score": 4,
                "reasoning": "Valid response after retries with proper score and reasoning fields present."
            })
        ]

        evaluator = JudgeEvaluator(
            llm_client=mock_llm_client,
            judge_model_id="openai/gpt-4o"
        )

        result = evaluator.evaluate_content(
            generated_article=sample_texts["generated"],
            ground_truth_article=sample_texts["ground_truth"]
        )

        # Should succeed after retries
        assert result.score == 4
        assert mock_llm_client.generate.call_count == 3

    def test_content_judge_max_retries_exceeded(self, mock_llm_client, sample_texts):
        """Test failure after max retries (2) exceeded."""
        from src.evaluator.metrics.judge import JudgeEvaluator

        # All responses are malformed
        mock_llm_client.generate.side_effect = [
            "Not JSON",
            "Still not JSON",
            "Never will be JSON"
        ]

        evaluator = JudgeEvaluator(
            llm_client=mock_llm_client,
            judge_model_id="openai/gpt-4o"
        )

        # Should raise after max retries
        with pytest.raises(RuntimeError, match="Failed to get valid judge response"):
            evaluator.evaluate_content(
                generated_article=sample_texts["generated"],
                ground_truth_article=sample_texts["ground_truth"]
            )

        # Should have tried 3 times (initial + 2 retries)
        assert mock_llm_client.generate.call_count == 3


class TestStyleJudgeEvaluator:
    """Test style judge evaluation logic.

    AICODE-NOTE: Tests JudgeEvaluator.evaluate_style() method
    AICODE-NOTE: Similar to content judge but compares generated vs source texts
    """

    @pytest.fixture
    def sample_texts(self):
        """Sample texts for testing."""
        return {
            "generated": "The cat sat on the mat. It was a warm, sunny afternoon.",
            "source_texts": "A feline lounged upon the plush rug. The weather proved delightfully temperate. Sunshine streamed through the windows, illuminating the cozy room.",
        }

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for testing."""
        return Mock()

    def test_style_judge_prompt_construction(self, mock_llm_client, sample_texts):
        """Test style judge prompt includes style comparison instructions."""
        from src.evaluator.metrics.judge import JudgeEvaluator

        # Mock LLM response
        mock_llm_client.generate.return_value = json.dumps({
            "score": 3,
            "reasoning": "TEXT_A attempts stylistic similarity but vocabulary and sentence structure differ significantly from TEXT_B reference style."
        })

        evaluator = JudgeEvaluator(
            llm_client=mock_llm_client,
            judge_model_id="openai/gpt-4o"
        )

        result = evaluator.evaluate_style(
            generated_article=sample_texts["generated"],
            source_texts=sample_texts["source_texts"]
        )

        # Verify LLM was called
        assert mock_llm_client.generate.called
        call_args = mock_llm_client.generate.call_args

        messages = call_args[1]["messages"]
        user_content = messages[1]["content"]

        # Check style judge instructions
        assert "TEXT_A" in user_content
        assert "TEXT_B" in user_content
        assert "style" in user_content.lower()
        assert "imitates" in user_content.lower() or "similarity" in user_content.lower()
        assert sample_texts["generated"] in user_content
        assert sample_texts["source_texts"] in user_content

    def test_style_judge_score_parsing(self, mock_llm_client, sample_texts):
        """Test parsing valid JSON response from style judge."""
        from src.evaluator.metrics.judge import JudgeEvaluator

        mock_llm_client.generate.return_value = json.dumps({
            "score": 4,
            "reasoning": "Generated text demonstrates good stylistic similarity with matching tone and vocabulary patterns. Sentence structure shows recognizable author voice."
        })

        evaluator = JudgeEvaluator(
            llm_client=mock_llm_client,
            judge_model_id="openai/gpt-4o"
        )

        result = evaluator.evaluate_style(
            generated_article=sample_texts["generated"],
            source_texts=sample_texts["source_texts"]
        )

        # Validate result
        assert isinstance(result, JudgeResult)
        assert result.score == 4
        assert "stylistic similarity" in result.reasoning or "style" in result.reasoning
        assert result.model == "openai/gpt-4o"
        assert result.prompt_version == "style_judge_v1"

    def test_style_judge_empty_texts(self, mock_llm_client):
        """Test style judge with empty texts returns None."""
        from src.evaluator.metrics.judge import JudgeEvaluator

        evaluator = JudgeEvaluator(
            llm_client=mock_llm_client,
            judge_model_id="openai/gpt-4o"
        )

        # Empty generated article
        result = evaluator.evaluate_style(
            generated_article="",
            source_texts="Some source text here"
        )
        assert result is None

        # Empty source texts
        result = evaluator.evaluate_style(
            generated_article="Some generated text",
            source_texts=""
        )
        assert result is None
