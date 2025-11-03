# AICODE-NOTE: T026, T027 - Pytest fixtures for testing
# AICODE-NOTE: T026 - Mock LLM client prevents real API calls in unit tests
# AICODE-NOTE: T027 - Temporary directories with auto-cleanup

"""Pytest configuration and shared fixtures for eval_harness tests.

Provides:
- Mock LLM client for testing without API calls
- Temporary directory fixtures with auto-cleanup
- Sample corpus and dataset paths
"""

from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_corpus_path() -> Path:
    """Path to sample corpus for testing.

    AICODE-NOTE: Points to fixtures/sample_corpus/ with 2 authors, 3 texts each
    AICODE-NOTE: Minimal corpus enables fast test execution
    """
    return Path(__file__).parent / "fixtures" / "sample_corpus"


@pytest.fixture
def mock_llm_client(mocker) -> MagicMock:
    """Mock LLM client that returns predefined responses.

    AICODE-NOTE: T026 - Prevents real API calls in unit tests
    AICODE-NOTE: Returns valid JSON responses matching expected schemas
    AICODE-NOTE: Configurable via mock.generate.return_value in tests

    Usage:
        def test_something(mock_llm_client):
            mock_llm_client.generate.return_value = '{"topic": "Test", "theses": [...]}'
            # Test code that uses LLM client
            mock_llm_client.generate.assert_called_once()
    """
    from src.shared.llm_client import LLMClient

    # AICODE-NOTE: Create mock that mimics LLMClient interface
    mock = mocker.patch('src.shared.llm_client.LLMClient')
    mock_instance = MagicMock(spec=LLMClient)

    # AICODE-NOTE: Default response for topic neutralization
    default_topic_response = {
        "topic": "Sample topic for testing",
        "theses": [
            "First thesis statement",
            "Second thesis statement",
            "Third thesis statement",
            "Fourth thesis statement",
            "Fifth thesis statement"
        ]
    }

    # AICODE-NOTE: Configure generate() to return JSON string
    import json
    mock_instance.generate.return_value = json.dumps(default_topic_response)

    # AICODE-NOTE: Configure parse_json_response() to return dict
    mock_instance.parse_json_response.return_value = default_topic_response

    mock.return_value = mock_instance
    return mock


@pytest.fixture
def mock_llm_response_topic() -> Dict[str, Any]:
    """Sample topic data for LLM responses.

    AICODE-NOTE: Valid TopicData structure for testing
    AICODE-NOTE: Matches schema from dataset_builder/config.py
    """
    return {
        "topic": "Journey through urban environment during weather event",
        "theses": [
            "Narrator is located in a city setting",
            "Weather conditions affect the experience",
            "Movement through urban space occurs",
            "Narrator observes architectural details",
            "Time of day influences the atmosphere",
            "Emotional response to environment is present"
        ]
    }


@pytest.fixture
def mock_llm_response_judge() -> Dict[str, Any]:
    """Sample judge result for LLM responses.

    AICODE-NOTE: Valid JudgeResult structure for testing
    AICODE-NOTE: Matches schema from evaluator/config.py
    """
    return {
        "score": 4,
        "reasoning": "The generated text demonstrates good coverage of the key themes and maintains similar stylistic elements. Minor differences in vocabulary choice and sentence structure prevent a perfect score, but overall quality is high."
    }


@pytest.fixture
def temp_dataset_dir(tmp_path) -> Path:
    """Temporary directory for dataset output.

    AICODE-NOTE: T027 - Auto-cleanup with pytest's tmp_path
    AICODE-NOTE: Creates fresh directory for each test
    AICODE-NOTE: Automatically removed after test completes

    Args:
        tmp_path: pytest built-in fixture for temporary directories

    Returns:
        Path to temporary dataset directory
    """
    dataset_dir = tmp_path / "eval_dataset"
    dataset_dir.mkdir(exist_ok=True)
    return dataset_dir


@pytest.fixture
def temp_results_dir(tmp_path) -> Path:
    """Temporary directory for evaluation results.

    AICODE-NOTE: T027 - Auto-cleanup with pytest's tmp_path
    AICODE-NOTE: Used for testing evaluation runner output

    Args:
        tmp_path: pytest built-in fixture for temporary directories

    Returns:
        Path to temporary results directory
    """
    results_dir = tmp_path / "eval_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


@pytest.fixture
def sample_topic_data() -> Dict[str, Any]:
    """Sample topic data for testing.

    AICODE-NOTE: Minimal valid TopicData for fast tests
    """
    return {
        "topic": "Test topic description",
        "theses": [
            "First key point",
            "Second key point",
            "Third key point",
            "Fourth key point",
            "Fifth key point"
        ]
    }


@pytest.fixture
def sample_dataset_config(sample_corpus_path, temp_dataset_dir) -> Dict[str, Any]:
    """Sample dataset configuration for testing.

    AICODE-NOTE: Valid DatasetConfig using sample corpus
    AICODE-NOTE: Uses minimum values for fast test execution
    """
    return {
        "corpus_path": str(sample_corpus_path),
        "output_path": str(temp_dataset_dir),
        "min_texts_per_author": 3,
        "m_style_texts": 1,
        "k_test_cases": 2,
        "neutralizer_model_id": "openai/gpt-4o-mini",
        "max_tokens_for_neutralizer": 4000,
        "random_seed": 42
    }


@pytest.fixture
def sample_eval_config(temp_dataset_dir, temp_results_dir) -> Dict[str, Any]:
    """Sample evaluation configuration for testing.

    AICODE-NOTE: Valid EvalConfig with all metrics enabled
    AICODE-NOTE: Uses fast models for testing
    """
    return {
        "dataset_path": str(temp_dataset_dir),
        "output_path": str(temp_results_dir),
        "generation_model_id": "openai/gpt-4o-mini",
        "judge_model_id": "openai/gpt-4o-mini",
        "metrics_numeric": {
            "cosine_similarity": True,
            "bert_score": True
        },
        "metrics_judge": {
            "content_judge": True,
            "style_judge": True
        },
        "embedding_model": "all-MiniLM-L6-v2",
        "llm_timeout": 60,
        "max_retries": 2
    }
