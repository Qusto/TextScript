# Research: StyleGuard Eval Harness

**Feature**: 003-style-eval-harness
**Date**: 2025-11-03
**Phase**: 0 - Outline & Research

## Overview

This document consolidates research findings for implementing StyleGuard, an automated evaluation harness for article generation quality. The research focuses on LLM integration patterns, text similarity metrics, evaluation methodologies, and CLI design best practices.

## Key Technology Decisions

### 1. LLM API Client Architecture

**Decision**: Unified LLM client with multi-provider support (OpenRouter/OpenAI/Anthropic)

**Rationale**:
- Existing project uses OpenRouter with OPENAI_API_KEY in .env
- Need flexibility to use different models for neutralization (Claude Sonnet) and judging (GPT-4o)
- Unified client reduces code duplication and provides consistent error handling
- OpenRouter supports both OpenAI and Anthropic models through single API

**Implementation Pattern**:
```python
# Reuse existing .env variables
OPENAI_API_KEY  # OpenRouter API key
MODEL           # Default model for generation

# Add new variables for evaluation
NEUTRALIZER_MODEL  # e.g., anthropic/claude-3-5-sonnet-20240620
JUDGE_MODEL        # e.g., openai/gpt-4o
```

**Alternatives Considered**:
- Separate clients for each provider → Rejected: More complexity, duplicate error handling
- Direct provider SDKs → Rejected: Requires multiple API keys, less flexible

### 2. Text Similarity Metrics

**Decision**: Combine numeric metrics (Cosine Similarity + BERTScore) with LLM-as-Judge

**Rationale**:
- **Cosine Similarity**: Fast, cheap, measures semantic similarity at document level
  - Library: sentence-transformers with `all-MiniLM-L6-v2` model
  - Pros: No API costs, reproducible, good for content drift detection
  - Cons: Doesn't capture style, limited understanding of nuance

- **BERTScore**: Token-level semantic matching with BERT embeddings
  - Library: bert-score (official implementation)
  - Pros: Better than BLEU/ROUGE for generative tasks, captures synonyms
  - Cons: Slower than cosine similarity, requires GPU for speed

- **LLM-as-Judge**: Qualitative evaluation by powerful LLMs
  - Pros: Understands style, tone, context that numeric metrics miss
  - Cons: Expensive, requires careful prompt engineering, less reproducible

**Combined Approach Benefits**:
- Numeric metrics provide fast regression detection
- LLM judges provide nuanced quality assessment
- Triangulating multiple metrics reduces false positives/negatives

**Alternatives Considered**:
- BLEU/ROUGE → Rejected: Poor for generative tasks, focus on n-gram overlap
- Only LLM judges → Rejected: Too expensive for large datasets, less reproducible
- Human evaluation → Rejected: Not scalable, defeats automation purpose

### 3. Configuration Management

**Decision**: YAML configuration files with Pydantic validation

**Rationale**:
- YAML more human-readable than JSON for config files
- Pydantic provides type validation and clear error messages
- Existing backend uses Pydantic for FastAPI models
- Easy to version control and share configuration presets

**Configuration Structure**:
```yaml
# dataset_config.yml
corpus_path: "./corpus/gutenberg/"
output_path: "./eval_dataset/"
min_texts_per_author: 10
m_style_texts: 5
k_test_cases: 5
neutralizer_model_id: "anthropic/claude-3-5-sonnet-20240620"
max_tokens_for_neutralizer: 4000

# eval_config.yml
dataset_path: "./eval_dataset/"
output_path: "./eval_results/"
generation_model_id: "meta-llama/llama-3-8b-instruct"
judge_model_id: "openai/gpt-4o"
metrics_numeric:
  cosine_similarity: true
  bert_score: true
metrics_judge:
  content_judge: true
  style_judge: true
embedding_model: "all-MiniLM-L6-v2"
```

**Alternatives Considered**:
- JSON config → Rejected: Less readable, no comments
- Command-line arguments only → Rejected: Too verbose for many parameters
- Python config files → Rejected: Security risk, harder to validate

### 4. CLI Design Patterns

**Decision**: Standard Python CLI with argparse, progress indicators (tqdm), structured logging (loguru)

**Rationale**:
- argparse is Python standard library, no extra dependencies
- tqdm provides user-friendly progress bars for long-running operations
- loguru already used in backend, provides colored output and structured logging
- Follow Unix philosophy: do one thing well, composable with pipes

**CLI Interface Pattern**:
```bash
# Dataset builder
python prepare_dataset.py [--config dataset_config.yml] [--verbose]

# Evaluator with filtering
python run_eval.py [--config eval_config.yml] [--author "mark_twain"] [--verbose]
```

**Alternatives Considered**:
- Click library → Rejected: Extra dependency, argparse sufficient for this use case
- Typer → Rejected: Same as Click, adds complexity for marginal benefit
- Interactive TUI → Rejected: Overkill, breaks scriptability

### 5. Ugly Script Integration

**Decision**: Import Ugly Script as library module with refactored API

**Rationale**:
- Ugly Script currently exists as standalone script
- Need to expose `analyze_style()` and `generate_article()` as callable functions
- Refactor to separate concerns: CLI vs. core logic
- Maintain backward compatibility with existing CLI

**Integration Pattern**:
```python
# In eval_harness/src/evaluator/integration.py
from src.ugly_script import analyze_style, generate_article

# Usage
style_profile = analyze_style(
    source_texts_content,
    model_id=config.generation_model_id
)

generated_article = generate_article(
    style_profile,
    topic_data=topic_json,
    model_id=config.generation_model_id
)
```

**Refactoring Required**:
- Extract core functions from ugly_script.py
- Add module-level API for programmatic use
- Keep existing CLI entry point functional
- Document public API for external use

**Alternatives Considered**:
- Subprocess calls to CLI → Rejected: Slow, hard to debug, fragile
- Copy-paste code → Rejected: Violates DRY, maintenance nightmare
- Rewrite generation logic → Rejected: Out of scope, unnecessary

### 6. Error Handling Strategy

**Decision**: Graceful degradation with detailed error logging

**Rationale**:
- LLM API calls can fail (rate limits, timeouts, network issues)
- Single test case failure should not stop entire evaluation run
- Need detailed logs for debugging but continue processing
- Retry logic with exponential backoff for transient failures

**Error Handling Patterns**:
```python
# For dataset generation (critical path)
try:
    neutralized_topic = neutralize_with_llm(text)
except APIError as e:
    logger.error(f"Failed to neutralize {filename}: {e}")
    # Retry with backoff
    neutralized_topic = retry_with_backoff(neutralize_with_llm, text)

# For evaluation (non-critical path)
try:
    judge_score = llm_judge_evaluate(generated, ground_truth)
except APIError as e:
    logger.warning(f"Judge evaluation failed for case {case_id}: {e}")
    judge_score = None  # Continue with other metrics
```

**Retry Strategy**:
- Max 3 retries with exponential backoff (1s, 2s, 4s)
- Retry on: rate limits (429), timeouts, server errors (5xx)
- Don't retry on: auth errors (401), bad request (400)

**Alternatives Considered**:
- Fail fast → Rejected: Wastes time on large datasets
- Infinite retries → Rejected: Can hang indefinitely
- Silent failures → Rejected: Hard to debug, masks issues

### 7. Test Strategy

**Decision**: Pytest with fixtures for test data, mock LLM calls in unit tests

**Rationale**:
- Existing project uses pytest
- Unit tests should not make real API calls (cost, speed, reliability)
- Integration tests with small sample corpus to validate end-to-end flow
- Contract tests to verify LLM prompt structure

**Test Structure**:
```python
# Unit tests with mocked LLM
@pytest.fixture
def mock_llm_client(mocker):
    mock = mocker.patch('src.shared.llm_client.LLMClient')
    mock.generate.return_value = {"topic": "Test", "theses": [...]}
    return mock

def test_neutralizer_extracts_topic(mock_llm_client):
    # Test logic without real API calls
    pass

# Integration tests with fixtures
def test_dataset_pipeline_end_to_end(tmp_path):
    # Use fixtures/sample_corpus/ as input
    # Verify output structure matches spec
    pass
```

**Test Coverage Goals**:
- Unit tests: >80% coverage for core logic
- Integration tests: Full pipeline validation
- Contract tests: LLM prompt validation

**Alternatives Considered**:
- VCR cassettes for API mocking → Rejected: Still requires initial API calls
- Manual testing only → Rejected: Not sustainable, breaks CI/CD
- No test fixtures → Rejected: Makes tests harder to maintain

## Dependencies to Add

**Required (Production)**:
```toml
[tool.poetry.dependencies]
pyyaml = "^6.0"                    # Config file parsing
sentence-transformers = "^2.2.0"   # Embeddings for cosine similarity
bert-score = "^0.3.13"             # Semantic similarity metric
pandas = "^2.0.0"                  # Data aggregation and CSV reports
tqdm = "^4.65.0"                   # Progress bars
# Already in backend: openai, loguru, pydantic, python-dotenv
```

**Development Only**:
```toml
[tool.poetry.group.dev.dependencies]
pytest-mock = "^3.11.0"            # Mocking for unit tests
# Already in backend: pytest, pytest-asyncio, pytest-cov
```

## Implementation Phases

### Phase 1: Core Infrastructure (P1 - MVP)
1. Set up eval_harness/ project structure with Poetry
2. Implement shared LLM client with .env integration
3. Implement dataset builder with neutralizer
4. Add unit tests for dataset builder
5. Validate with small corpus (2-3 authors, 5 texts each)

### Phase 2: Evaluation Engine (P2)
1. Implement numeric metrics (cosine similarity, BERTScore)
2. Implement LLM-as-Judge metrics
3. Implement evaluation runner with progress tracking
4. Add integration tests for full pipeline
5. Validate with generated dataset from Phase 1

### Phase 3: Reporting & Polish (P3)
1. Implement aggregation and summary reports (CSV, Markdown)
2. Add author filtering and selective evaluation
3. Improve error handling and logging
4. Write documentation (README, quickstart)
5. Performance optimization if needed

## Open Questions (Resolved)

All technical clarifications have been resolved through existing project inspection:

✅ **LLM API Integration**: Reuse existing OpenRouter setup with .env configuration
✅ **Test Framework**: Use pytest matching backend conventions
✅ **Logging**: Use loguru already in backend dependencies
✅ **Configuration Format**: YAML with Pydantic validation
✅ **CLI Framework**: Standard argparse, no additional dependencies
✅ **Ugly Script Integration**: Import as module after refactoring to expose API

## Next Steps

Proceed to Phase 1 design:
1. Generate data-model.md defining file formats and data structures
2. Generate CLI contracts for both tools
3. Generate LLM prompt contracts for neutralizer and judges
4. Create quickstart.md with setup and usage instructions
