# AICODE-NOTE: Unit tests for LLM client (T012-T014)
# AICODE-NOTE: Tests initialization, retry logic, and JSON parsing

"""Unit tests for shared/llm_client.py"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.shared.llm_client import LLMClient
from src.dataset_builder.config import TopicData


def test_llm_client_initialization():
    """Test LLMClient initializes with .env API key.

    AICODE-NOTE: Tests T012 - initialization with .env loading
    """
    # AICODE-NOTE: Use repository root .env (should exist)
    client = LLMClient(timeout=60, max_retries=2)

    assert client.api_key is not None
    assert client.timeout == 60
    assert client.max_retries == 2


def test_llm_client_missing_api_key(monkeypatch, tmp_path):
    """Test LLMClient raises error when API key missing.

    AICODE-NOTE: Tests T012 - error handling for missing credentials
    """
    # AICODE-NOTE: Remove API key from environment
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # AICODE-NOTE: Point to non-existent .env file
    fake_env = tmp_path / ".env"

    with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
        LLMClient(env_path=fake_env)


def test_parse_json_response_valid():
    """Test JSON parsing with valid response.

    AICODE-NOTE: Tests T014 - basic JSON parsing
    """
    client = LLMClient()

    response = '{"topic": "Test", "theses": ["one", "two", "three", "four", "five"]}'
    result = client.parse_json_response(response)

    assert result["topic"] == "Test"
    assert len(result["theses"]) == 5


def test_parse_json_response_with_markdown():
    """Test JSON parsing with markdown code blocks.

    AICODE-NOTE: Tests T014 - handles Claude's markdown formatting
    """
    client = LLMClient()

    # AICODE-NOTE: Claude often wraps JSON in ```json blocks
    response = '```json\n{"topic": "Test", "theses": ["one", "two", "three", "four", "five"]}\n```'
    result = client.parse_json_response(response)

    assert result["topic"] == "Test"
    assert len(result["theses"]) == 5


def test_parse_json_response_with_explanatory_text():
    """Test JSON parsing with surrounding text.

    AICODE-NOTE: Tests T014 - handles GPT's explanatory text
    """
    client = LLMClient()

    # AICODE-NOTE: GPT sometimes adds explanations before/after JSON
    response = 'Here is the JSON:\n\n{"topic": "Test", "theses": ["one", "two", "three", "four", "five"]}\n\nHope this helps!'
    result = client.parse_json_response(response)

    assert result["topic"] == "Test"
    assert len(result["theses"]) == 5


def test_parse_json_response_with_schema_validation():
    """Test JSON parsing with Pydantic schema validation.

    AICODE-NOTE: Tests T014 - schema validation integration
    """
    client = LLMClient()

    response = '{"topic": "Test topic", "theses": ["one", "two", "three", "four", "five"]}'
    result = client.parse_json_response(response, schema=TopicData)

    assert result["topic"] == "Test topic"
    assert len(result["theses"]) == 5


def test_parse_json_response_invalid_json():
    """Test JSON parsing with malformed JSON.

    AICODE-NOTE: Tests T014 - error handling for invalid JSON
    """
    client = LLMClient()

    response = 'This is not JSON at all!'

    with pytest.raises(ValueError, match="No JSON object found"):
        client.parse_json_response(response)


def test_parse_json_response_schema_validation_failure():
    """Test JSON parsing with schema validation failure.

    AICODE-NOTE: Tests T014 - schema validation error handling
    """
    client = LLMClient()

    # AICODE-NOTE: Invalid TopicData - missing theses field
    response = '{"topic": "Test"}'

    with pytest.raises(ValueError, match="doesn't match expected schema"):
        client.parse_json_response(response, schema=TopicData)
