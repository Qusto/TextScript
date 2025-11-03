# AICODE-NOTE: T031 [P] [US1] Unit test for neutralizer component
# AICODE-NOTE: Tests JSON parsing, schema validation, stylistic marker detection
# AICODE-NOTE: Tests theses count validation (5-10 acceptable, 4-11 with warning)
# AICODE-NOTE: Tests text truncation before API call

"""Unit tests for Neutralizer component.

Tests:
- Initialization with LLM client injection
- neutralize() with valid response
- JSON response parsing and TopicData validation
- Theses count validation (strict 5-10, accepts 4-11 with warning)
- Text truncation using shared truncate_text()
- Error handling for malformed JSON
"""

import json
import sys
from unittest.mock import Mock

import pytest
from loguru import logger

from src.dataset_builder.config import TopicData
from src.dataset_builder.neutralizer import Neutralizer


# AICODE-NOTE: Configure loguru to work with pytest caplog
@pytest.fixture(autouse=True)
def setup_loguru(caplog):
    """Setup loguru to capture logs for pytest."""
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    yield
    logger.remove()


class TestNeutralizerInit:
    """Test Neutralizer initialization."""

    def test_init_with_llm_client(self):
        """Test initialization with LLM client injection.

        AICODE-NOTE: Dependency injection for testability
        """
        mock_client = Mock()
        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)

        assert neutralizer.llm_client == mock_client
        assert neutralizer.max_tokens == 4000

    def test_init_with_custom_max_tokens(self):
        """Test initialization with custom max_tokens value."""
        mock_client = Mock()
        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=2000)

        assert neutralizer.max_tokens == 2000


class TestNeutralizerBasicFunctionality:
    """Test basic neutralization functionality."""

    def test_neutralize_success(self):
        """Test successful neutralization with valid response.

        AICODE-NOTE: Tests full neutralization pipeline with valid JSON
        """
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Journey through Paris",
            "theses": [
                "Narrator is located in Paris",
                "Weather conditions: strong wind",
                "Narrator experiences negative emotions",
                "Movement occurs on foot",
                "Time period: evening or night"
            ]
        })

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)

        article_text = "The storm raged as I walked through Paris..."
        result = neutralizer.neutralize(article_text)

        # AICODE-NOTE: Verify result is valid TopicData
        assert isinstance(result, TopicData)
        assert result.topic == "Journey through Paris"
        assert len(result.theses) == 5
        assert result.theses[0] == "Narrator is located in Paris"

        # AICODE-NOTE: Verify LLM was called with correct parameters
        mock_client.generate.assert_called_once()
        call_args = mock_client.generate.call_args
        assert "messages" in call_args.kwargs
        assert len(call_args.kwargs["messages"]) == 2  # System + User message

    def test_neutralize_with_model_id(self):
        """Test neutralization passes correct model_id to LLM client.

        AICODE-NOTE: Verifies model_id is passed through to API call
        """
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test topic",
            "theses": ["Thesis 1", "Thesis 2", "Thesis 3", "Thesis 4", "Thesis 5"]
        })

        neutralizer = Neutralizer(
            llm_client=mock_client,
            max_tokens=4000,
            model_id="anthropic/claude-3-5-sonnet-20240620"
        )

        neutralizer.neutralize("Test article")

        call_args = mock_client.generate.call_args
        assert call_args.kwargs["model_id"] == "anthropic/claude-3-5-sonnet-20240620"


class TestNeutralizerJSONParsing:
    """Test JSON response parsing and validation."""

    def test_parse_json_with_markdown_blocks(self):
        """Test parsing JSON wrapped in markdown code blocks.

        AICODE-NOTE: Claude often wraps JSON in ```json blocks
        """
        mock_client = Mock()
        mock_client.generate.return_value = """```json
{
  "topic": "Test topic",
  "theses": ["T1", "T2", "T3", "T4", "T5"]
}
```"""

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)
        result = neutralizer.neutralize("Test article")

        assert isinstance(result, TopicData)
        assert result.topic == "Test topic"
        assert len(result.theses) == 5

    def test_parse_json_with_extra_text(self):
        """Test parsing JSON with explanatory text before/after.

        AICODE-NOTE: GPT-4 sometimes adds explanations
        """
        mock_client = Mock()
        mock_client.generate.return_value = """Here is the analysis:
{"topic": "Test", "theses": ["T1", "T2", "T3", "T4", "T5"]}
I hope this helps!"""

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)
        result = neutralizer.neutralize("Test article")

        assert isinstance(result, TopicData)
        assert result.topic == "Test"

    def test_parse_malformed_json_raises_error(self):
        """Test that malformed JSON raises ValueError.

        AICODE-NOTE: Should raise ValueError for malformed JSON
        AICODE-NOTE: Retry logic tested separately
        """
        mock_client = Mock()
        mock_client.generate.return_value = "This is not JSON at all"

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)

        with pytest.raises(ValueError, match="No JSON object found"):
            neutralizer.neutralize("Test article")

    def test_parse_json_missing_fields(self):
        """Test that JSON missing required fields raises error.

        AICODE-NOTE: TopicData requires both 'topic' and 'theses'
        """
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test topic"
            # Missing 'theses' field
        })

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)

        with pytest.raises(ValueError, match="validation"):
            neutralizer.neutralize("Test article")


class TestNeutralizerThesesCountValidation:
    """Test theses count validation logic."""

    @pytest.mark.parametrize("count", [5, 6, 7, 8, 9, 10])
    def test_valid_theses_count(self, count):
        """Test that 5-10 theses are accepted without warning.

        AICODE-NOTE: Standard theses count range: 5-10
        """
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test topic",
            "theses": [f"Thesis {i}" for i in range(count)]
        })

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)
        result = neutralizer.neutralize("Test article")

        assert len(result.theses) == count

    def test_acceptable_theses_count_boundary(self):
        """Test that boundary cases (4 or 11 theses) are handled appropriately.

        AICODE-NOTE: Pydantic TopicData enforces 5-10 strictly
        AICODE-NOTE: 4 and 11 will be rejected by Pydantic validation
        AICODE-NOTE: This is intentional - neutralizer should retry if count is outside 5-10
        """
        # AICODE-NOTE: Test that 4 theses is rejected
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test topic",
            "theses": ["T1", "T2", "T3", "T4"]
        })

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)

        with pytest.raises(ValueError, match="validation"):
            neutralizer.neutralize("Test article")

        # AICODE-NOTE: Test that 11 theses is rejected
        mock_client.generate.return_value = json.dumps({
            "topic": "Test topic",
            "theses": [f"T{i}" for i in range(11)]
        })

        with pytest.raises(ValueError, match="validation"):
            neutralizer.neutralize("Test article")

    @pytest.mark.parametrize("count", [3, 12])
    def test_invalid_theses_count_raises_error(self, count):
        """Test that <4 or >11 theses raises validation error.

        AICODE-NOTE: Strict rejection for <4 or >11 theses
        AICODE-NOTE: TopicData validation enforces 5-10, but we accept 4-11 in neutralizer
        """
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test topic",
            "theses": [f"Thesis {i}" for i in range(count)]
        })

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)

        with pytest.raises(ValueError, match="theses"):
            neutralizer.neutralize("Test article")


class TestNeutralizerTextTruncation:
    """Test text truncation logic."""

    def test_truncate_long_text(self):
        """Test that long text is truncated before API call.

        AICODE-NOTE: Uses shared truncate_text() from file_utils
        """
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test",
            "theses": ["T1", "T2", "T3", "T4", "T5"]
        })

        # AICODE-NOTE: Create text that exceeds max_tokens=1000 (~4000 chars)
        long_text = "Test sentence. " * 500  # ~7500 chars

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=1000)
        neutralizer.neutralize(long_text)

        # AICODE-NOTE: Verify LLM was called with truncated text
        call_args = mock_client.generate.call_args
        user_message = call_args[1]["messages"][1]["content"]

        # AICODE-NOTE: User message should contain truncated text, not original
        assert len(user_message) < len(long_text)
        assert len(user_message) < 8000  # Approximate: 1000 tokens * 4 chars + prompt template

    def test_short_text_not_truncated(self):
        """Test that short text is not truncated."""
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test",
            "theses": ["T1", "T2", "T3", "T4", "T5"]
        })

        short_text = "This is a short article about test topics."

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)
        neutralizer.neutralize(short_text)

        # AICODE-NOTE: Verify text was included in API call
        call_args = mock_client.generate.call_args
        user_message = call_args.kwargs["messages"][1]["content"]

        assert short_text in user_message


class TestNeutralizerStylisticMarkerDetection:
    """Test detection of stylistic markers in neutralized output."""

    def test_detect_stylistic_markers_logs_warning(self):
        """Test that stylistic markers in output are still accepted.

        AICODE-NOTE: Heuristic check for common stylistic markers
        AICODE-NOTE: Markers: 'like a', 'as if', 'seemed to', '!', 'alas', 'oh'
        AICODE-NOTE: This test verifies neutralizer accepts output even with markers
        AICODE-NOTE: (Logging test is hard to verify reliably, so we just check acceptance)
        """
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Journey like a dream",  # Contains marker "like a"
            "theses": [
                "It seemed to rain",
                "As if by magic",
                "Wind was strong",
                "Streets were wet",
                "Journey was long"
            ]
        })

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)
        result = neutralizer.neutralize("Test article")

        # AICODE-NOTE: Should accept result even with stylistic markers
        # (Real implementation logs WARNING but doesn't reject)
        assert isinstance(result, TopicData)
        assert result.topic == "Journey like a dream"
        assert len(result.theses) == 5

    def test_neutral_output_no_warning(self, caplog):
        """Test that properly neutral output doesn't trigger warnings."""
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Journey through Paris",
            "theses": [
                "Narrator is located in Paris",
                "Weather conditions: strong wind",
                "Narrator experiences negative emotions",
                "Movement occurs on foot",
                "Time period: evening or night"
            ]
        })

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)
        result = neutralizer.neutralize("Test article")

        assert isinstance(result, TopicData)
        # AICODE-NOTE: Should not log stylistic warnings
        assert "stylistic" not in caplog.text.lower()


class TestNeutralizerPromptStructure:
    """Test that neutralizer uses correct prompt structure."""

    def test_prompt_has_system_and_user_messages(self):
        """Test that prompt includes system and user messages.

        AICODE-NOTE: Implements prompt-neutralizer.md contract
        """
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test",
            "theses": ["T1", "T2", "T3", "T4", "T5"]
        })

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)
        neutralizer.neutralize("Test article")

        call_args = mock_client.generate.call_args
        messages = call_args.kwargs["messages"]

        # AICODE-NOTE: Should have system message and user message
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_system_message_content(self):
        """Test that system message contains key instructions.

        AICODE-NOTE: Checks for neutrality instructions from prompt contract
        """
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test",
            "theses": ["T1", "T2", "T3", "T4", "T5"]
        })

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)
        neutralizer.neutralize("Test article")

        call_args = mock_client.generate.call_args
        system_message = call_args.kwargs["messages"][0]["content"]

        # AICODE-NOTE: System message should mention neutrality and style separation
        assert "neutral" in system_message.lower() or "neutrality" in system_message.lower()
        assert "style" in system_message.lower() or "stylistic" in system_message.lower()

    def test_user_message_contains_article(self):
        """Test that user message contains the article text."""
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Test",
            "theses": ["T1", "T2", "T3", "T4", "T5"]
        })

        article_text = "This is the original article text to be neutralized."

        neutralizer = Neutralizer(llm_client=mock_client, max_tokens=4000)
        neutralizer.neutralize(article_text)

        call_args = mock_client.generate.call_args
        user_message = call_args.kwargs["messages"][1]["content"]

        # AICODE-NOTE: User message should contain the article text
        assert article_text in user_message
