# Contributing to StyleGuard Eval Harness

**AICODE-NOTE: T125 - Development guidelines for extending functionality**

Thank you for considering contributing to StyleGuard! This guide will help you understand the codebase structure and how to add new features.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Adding New Features](#adding-new-features)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Poetry 1.7+
- Git

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/TextScript.git
   cd TextScript/eval_harness
   ```

2. **Install dependencies** (including dev dependencies):
   ```bash
   poetry install
   ```

3. **Install pre-commit hooks** (optional but recommended):
   ```bash
   poetry run pre-commit install
   ```

4. **Set up environment**:
   ```bash
   # Copy example .env to repository root
   cp ../.env.example ../.env
   # Edit .env and add your API keys
   ```

5. **Run tests to verify setup**:
   ```bash
   poetry run pytest -v
   ```

### Development Tools

```bash
# Run linter
poetry run ruff check src/

# Format code
poetry run ruff format src/

# Type checking
poetry run mypy src/

# Run tests with coverage
poetry run pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Project Architecture

### Directory Structure

```text
eval_harness/
├── src/                          # Source code
│   ├── shared/                   # Shared utilities
│   │   ├── llm_client.py        # Unified LLM API client
│   │   └── file_utils.py        # File I/O helpers
│   ├── dataset_builder/          # Dataset generation (US1)
│   │   ├── config.py            # DatasetConfig model
│   │   ├── neutralizer.py       # Topic neutralization
│   │   └── builder.py           # Main dataset builder
│   └── evaluator/                # Quality evaluation (US2)
│       ├── config.py            # EvalConfig model
│       ├── integration.py       # Ugly Script adapter
│       ├── runner.py            # Evaluation orchestrator
│       ├── aggregator.py        # Results aggregation
│       └── metrics/
│           ├── numeric.py       # Cosine + BERTScore
│           └── judge.py         # LLM-as-Judge
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test data
├── configs/                      # Example configurations
├── examples/                     # Example scripts
├── prepare_dataset.py           # CLI: Dataset builder
└── run_eval.py                  # CLI: Evaluator
```

### Key Design Patterns

1. **Dependency Injection**: Components accept dependencies in `__init__()` for testability
2. **Pydantic Models**: All configuration uses Pydantic for validation
3. **Error Recovery**: Individual failures don't crash entire pipeline
4. **Progressive Enhancement**: Features are optional (enable/disable metrics)

### Core Components

#### LLMClient (`src/shared/llm_client.py`)

**Purpose**: Unified interface for OpenRouter, OpenAI, and Anthropic APIs

**Key Methods**:
- `generate()` - Make LLM API call with retry logic
- `parse_json_response()` - Parse and validate JSON from LLM

**How to use**:
```python
from src.shared.llm_client import LLMClient

client = LLMClient(timeout=120, max_retries=3)
response = client.generate(
    model_id="openai/gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello!"}
    ],
    temperature=0.7,
    max_tokens=100
)
print(response)
```

#### DatasetBuilder (`src/dataset_builder/builder.py`)

**Purpose**: Generate test datasets from text corpus

**Key Methods**:
- `scan_corpus()` - Discover authors and texts
- `generate_dataset()` - Main orchestration loop
- `_create_case()` - Generate single test case

#### EvaluationRunner (`src/evaluator/runner.py`)

**Purpose**: Run evaluation on test dataset

**Key Methods**:
- `run_evaluation()` - Main orchestration
- `_evaluate_case()` - Evaluate single test case
- `_load_test_cases()` - Load dataset

---

## Adding New Features

### Adding a New Metric

Let's add a new metric (e.g., "Readability Score") to the evaluator.

#### Step 1: Update Config Model

Edit `src/evaluator/config.py`:

```python
class EvalConfig(BaseModel):
    # ... existing fields ...

    metrics_numeric: Dict[str, bool] = Field(
        default={
            "cosine_similarity": True,
            "bert_score": True,
            "readability_score": False,  # NEW METRIC
        }
    )
```

#### Step 2: Implement Metric Calculator

Create or edit `src/evaluator/metrics/numeric.py`:

```python
# AICODE-NOTE: New metric - Readability score using textstat library

from textstat import flesch_reading_ease

class NumericMetrics:
    # ... existing methods ...

    def compute_readability(
        self,
        text1: str,
        text2: str
    ) -> Optional[float]:
        """Compute readability score difference between two texts.

        Args:
            text1: Reference text (ground truth)
            text2: Generated text

        Returns:
            Normalized similarity score [0.0-1.0], where 1.0 means
            identical readability levels

        AICODE-NOTE: Uses Flesch Reading Ease score
        AICODE-NOTE: Converts absolute difference to similarity score
        """
        try:
            score1 = flesch_reading_ease(text1)
            score2 = flesch_reading_ease(text2)

            # AICODE-NOTE: Convert difference to similarity
            # Max difference is 100, normalize to [0, 1]
            diff = abs(score1 - score2)
            similarity = 1.0 - (diff / 100.0)

            return max(0.0, similarity)

        except Exception as e:
            logger.warning(f"Readability computation failed: {e}")
            return None
```

#### Step 3: Integrate into Runner

Edit `src/evaluator/runner.py`:

```python
class EvaluationRunner:
    def _evaluate_case(self, test_case: Dict, perfect_test: bool = False) -> Dict:
        # ... existing code ...

        # AICODE-NOTE: Compute new readability metric if enabled
        if self.config.metrics_numeric.get("readability_score", False):
            readability = self.numeric_metrics.compute_readability(
                ground_truth_text,
                generated_text
            )

            if readability is not None:
                metrics["readability_score"] = readability

                # Save to separate JSON file
                readability_file = case_dir / "metric_readability.json"
                with open(readability_file, 'w') as f:
                    json.dump({
                        "readability_score": readability,
                        "computed_at": datetime.now().isoformat()
                    }, f, indent=2)

        return metrics
```

#### Step 4: Update Aggregator

Edit `src/evaluator/aggregator.py`:

```python
class ResultAggregator:
    def aggregate_results(self, output_dir: Path) -> Dict:
        # ... existing code ...

        # AICODE-NOTE: Include readability in aggregation
        if "readability_score" in all_metrics.columns:
            summary["mean_metrics"]["readability_score"] = \
                all_metrics["readability_score"].mean()
            summary["median_metrics"]["readability_score"] = \
                all_metrics["readability_score"].median()

        return summary
```

#### Step 5: Add Tests

Create `tests/unit/test_readability_metric.py`:

```python
# AICODE-NOTE: Unit tests for new readability metric

import pytest
from src.evaluator.metrics.numeric import NumericMetrics

def test_readability_identical_texts():
    """Test readability score for identical texts."""
    metrics = NumericMetrics()
    text = "The quick brown fox jumps over the lazy dog."

    score = metrics.compute_readability(text, text)

    assert score is not None
    assert score >= 0.95  # Nearly perfect match

def test_readability_different_complexity():
    """Test readability score for texts with different complexity."""
    metrics = NumericMetrics()

    simple = "The cat sat on the mat."
    complex = "The feline quadruped positioned itself atop the textile surface covering."

    score = metrics.compute_readability(simple, complex)

    assert score is not None
    assert 0.0 <= score <= 1.0
    assert score < 0.9  # Different complexity should have lower score
```

Run tests:
```bash
poetry run pytest tests/unit/test_readability_metric.py -v
```

#### Step 6: Update Documentation

Edit `README.md` and `CHANGELOG.md` to document the new metric.

### Adding a New LLM Provider

Let's add support for Cohere API.

#### Step 1: Add Client Initialization

Edit `src/shared/llm_client.py`:

```python
# AICODE-NOTE: Add Cohere support
from cohere import Client as CohereClient

class LLMClient:
    def __init__(self, ...):
        # ... existing code ...
        self._cohere_client: Optional[CohereClient] = None

    def _get_cohere_client(self) -> CohereClient:
        """Get or create Cohere client."""
        if self._cohere_client is None:
            # AICODE-NOTE: Reuse OPENAI_API_KEY or add COHERE_API_KEY
            api_key = os.getenv("COHERE_API_KEY") or self.api_key
            self._cohere_client = CohereClient(api_key=api_key)
            logger.debug("Initialized Cohere client")
        return self._cohere_client
```

#### Step 2: Add Generate Method

```python
class LLMClient:
    def generate(self, model_id: str, messages: List[Dict], ...) -> str:
        # ... existing routing code ...

        # AICODE-NOTE: Route Cohere models
        if model_id.startswith("cohere/"):
            response = self._call_cohere(
                model_id.replace("cohere/", ""),
                messages,
                temperature,
                max_tokens
            )

        # ... existing code ...

    def _call_cohere(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call Cohere API.

        AICODE-NOTE: Cohere uses different message format:
        - Only supports single prompt (not multi-turn)
        - Combine messages into single prompt
        """
        client = self._get_cohere_client()

        # AICODE-NOTE: Convert messages to single prompt
        prompt = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages
        ])

        response = client.generate(
            model=model_id,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.generations[0].text
```

#### Step 3: Add Tests

```python
def test_cohere_generation(mocker):
    """Test Cohere API call."""
    mock_client = mocker.patch('cohere.Client')
    mock_client.return_value.generate.return_value.generations = [
        mocker.Mock(text="Hello from Cohere!")
    ]

    client = LLMClient()
    response = client.generate(
        model_id="cohere/command-r-plus",
        messages=[{"role": "user", "content": "Say hello"}]
    )

    assert response == "Hello from Cohere!"
```

### Adding a New CLI Flag

Let's add a `--dry-run` flag to dataset builder.

#### Step 1: Add Argparse Flag

Edit `prepare_dataset.py`:

```python
def main() -> int:
    parser = argparse.ArgumentParser(...)

    # ... existing arguments ...

    # AICODE-NOTE: New flag - dry-run mode
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate dataset generation without making API calls"
    )

    args = parser.parse_args()
```

#### Step 2: Pass to Builder

```python
def main() -> int:
    # ... existing code ...

    builder = DatasetBuilder(
        config=config,
        llm_client=llm_client,
        dry_run=args.dry_run  # NEW PARAMETER
    )

    builder.generate_dataset()
```

#### Step 3: Implement in Builder

Edit `src/dataset_builder/builder.py`:

```python
class DatasetBuilder:
    def __init__(
        self,
        config: DatasetConfig,
        llm_client: LLMClient,
        dry_run: bool = False  # NEW PARAMETER
    ):
        self.config = config
        self.llm_client = llm_client
        self.dry_run = dry_run

        if self.dry_run:
            logger.warning("DRY-RUN mode enabled - no API calls will be made")

    def _create_case(self, ...):
        if self.dry_run:
            # AICODE-NOTE: Skip API call in dry-run mode
            logger.info(f"DRY-RUN: Would neutralize {test_file.name}")
            topic_data = {
                "topic": "Sample Topic (dry-run)",
                "theses": ["Thesis 1", "Thesis 2", "Thesis 3", "Thesis 4", "Thesis 5"]
            }
        else:
            # Normal API call
            topic_data = self.neutralizer.neutralize(...)

        # ... rest of case creation ...
```

---

## Code Style Guidelines

### Python Style

Follow PEP 8 with these specific conventions:

- **Line length**: 88 characters (Black default)
- **Imports**: Use `isort` order (stdlib → third-party → local)
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all classes and public methods

### AICODE Comments

**All non-trivial code must include AICODE comments**:

```python
# AICODE-NOTE: Brief explanation of why this approach was chosen
# AICODE-TODO: Future improvements or planned refactoring
# AICODE-ASK: Questions requiring human input or clarification
# AICODE-FIX: Technical debt or temporary workarounds
```

**When to use**:
- Architectural decisions: "Why this pattern?"
- Algorithm choices: "Why this approach over alternatives?"
- Edge cases: "Why handle this specific case?"
- Integration points: "How this connects to other systems?"

**Good examples**:
```python
# AICODE-NOTE: Using MD5 for cache keys (not security-critical, faster than SHA256)
cache_key = hashlib.md5(text.encode()).hexdigest()

# AICODE-TODO: Add exponential backoff for rate limit handling
time.sleep(1)

# AICODE-ASK: Should we validate URL format strictly or allow relative paths?
if url.startswith("http"):
    ...

# AICODE-FIX: Temporary workaround for circular import - refactor into separate module
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import User
```

### Error Handling

```python
# Good: Specific error handling with recovery
try:
    result = self.llm_client.generate(...)
except ValueError as e:
    logger.error(f"Invalid API request: {e}")
    return None  # Graceful degradation
except RuntimeError as e:
    logger.error(f"API call failed: {e}")
    raise  # Re-raise critical errors

# Bad: Catching all exceptions
try:
    result = self.llm_client.generate(...)
except Exception:
    pass  # Silent failures are bad!
```

### Logging

```python
# Use appropriate log levels
logger.debug("Detailed info for debugging")
logger.info("Normal operation milestone")
logger.success("Operation completed successfully")
logger.warning("Potential issue, but continuing")
logger.error("Error occurred, but recovered")
logger.exception("Critical error with traceback")

# Include context in log messages
logger.info(f"Processing author: {author_name} ({text_count} texts)")
logger.error(f"Failed to parse JSON from model {model_id}: {error}")
```

---

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 80% for new code
- **Critical paths**: 100% coverage (LLMClient, config validation)

### Test Organization

```text
tests/
├── unit/                   # Fast, isolated tests
│   ├── test_builder.py    # DatasetBuilder tests
│   ├── test_neutralizer.py
│   └── test_metrics.py
├── integration/            # End-to-end tests
│   ├── test_dataset_pipeline.py
│   └── test_eval_pipeline.py
└── fixtures/              # Test data
    └── sample_corpus/
```

### Writing Good Tests

#### Unit Test Example

```python
# AICODE-NOTE: Unit test for Neutralizer JSON parsing

import pytest
from src.dataset_builder.neutralizer import Neutralizer

def test_neutralizer_parses_valid_json(mocker):
    """Test that Neutralizer correctly parses valid JSON response."""
    # AICODE-NOTE: Mock LLM client to avoid real API calls
    mock_client = mocker.Mock()
    mock_client.generate.return_value = '''
    {
        "topic": "The Role of Technology",
        "theses": ["Thesis 1", "Thesis 2", "Thesis 3", "Thesis 4", "Thesis 5"]
    }
    '''

    neutralizer = Neutralizer(
        llm_client=mock_client,
        model_id="test-model",
        max_tokens=1000
    )

    result = neutralizer.neutralize("Sample text content")

    assert result["topic"] == "The Role of Technology"
    assert len(result["theses"]) == 5
    mock_client.generate.assert_called_once()

def test_neutralizer_handles_malformed_json(mocker):
    """Test that Neutralizer retries on malformed JSON."""
    mock_client = mocker.Mock()
    mock_client.generate.side_effect = [
        "Not valid JSON",  # First attempt fails
        '{"topic": "Valid", "theses": ["T1", "T2", "T3", "T4", "T5"]}'  # Retry succeeds
    ]

    neutralizer = Neutralizer(mock_client, "test-model", 1000)
    result = neutralizer.neutralize("Sample text")

    assert result["topic"] == "Valid"
    assert mock_client.generate.call_count == 2
```

#### Integration Test Example

```python
# AICODE-NOTE: Integration test for full dataset generation

def test_dataset_generation_end_to_end(tmp_path, mock_llm_client):
    """Test complete dataset generation pipeline."""
    # Setup
    corpus_path = tmp_path / "corpus"
    output_path = tmp_path / "output"

    # Create sample corpus
    author_dir = corpus_path / "test_author"
    author_dir.mkdir(parents=True)
    for i in range(10):
        (author_dir / f"text_{i}.txt").write_text(f"Sample text {i}")

    # Configure
    config = DatasetConfig(
        corpus_path=str(corpus_path),
        output_path=str(output_path),
        min_texts_per_author=10,
        m_style_texts=5,
        k_test_cases=3
    )

    # Execute
    builder = DatasetBuilder(config=config, llm_client=mock_llm_client)
    builder.generate_dataset()

    # Verify
    assert output_path.exists()
    author_output = output_path / "test_author"
    assert author_output.exists()

    case_dirs = list(author_output.glob("case_*"))
    assert len(case_dirs) == 3

    for case_dir in case_dirs:
        assert (case_dir / "source_texts.txt").exists()
        assert (case_dir / "ground_truth_article.txt").exists()
        assert (case_dir / "topic.json").exists()
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/unit/test_builder.py -v

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run only integration tests
poetry run pytest tests/integration/ -v

# Run tests matching pattern
poetry run pytest -k "neutralizer" -v

# Stop on first failure
poetry run pytest -x
```

---

## Submitting Changes

### Before Submitting

1. **Run linter**:
   ```bash
   poetry run ruff check src/
   poetry run ruff format src/
   ```

2. **Run type checker**:
   ```bash
   poetry run mypy src/
   ```

3. **Run tests**:
   ```bash
   poetry run pytest --cov=src
   ```

4. **Update CHANGELOG.md**:
   ```markdown
   ## [Unreleased]

   ### Added
   - New readability metric for evaluator (#123)

   ### Fixed
   - Neutralizer retry logic for malformed JSON (#124)
   ```

5. **Update documentation**:
   - README.md if user-facing changes
   - Docstrings for new functions
   - AICODE comments for all non-trivial code

### Pull Request Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing
- [ ] Coverage ≥80%

## Checklist

- [ ] Code follows style guidelines (ruff, mypy)
- [ ] AICODE comments added for all non-trivial code
- [ ] Documentation updated (README, docstrings)
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
```

### Commit Message Format

```text
type(scope): brief description

Detailed explanation if needed.

AICODE-NOTE: Explanation of implementation approach.

Closes #123
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding or updating tests
- `chore`: Maintenance (dependencies, config)

**Examples**:
```text
feat(metrics): add readability score metric

Implements Flesch Reading Ease score comparison between
ground truth and generated articles. Metric is optional
and can be enabled in eval_config.yml.

AICODE-NOTE: Uses textstat library for readability computation.

Closes #42
```

```text
fix(neutralizer): handle markdown-wrapped JSON responses

Some LLM models (Claude) wrap JSON in markdown code blocks.
Updated parser to strip ```json and ``` markers.

AICODE-NOTE: Also handles models that add explanatory text
before/after JSON object.

Fixes #56
```

---

## Questions?

- **Architecture questions**: See [plan.md](../specs/003-style-eval-harness/plan.md)
- **API contracts**: See [contracts/](../specs/003-style-eval-harness/contracts/)
- **Usage questions**: See [README.md](./README.md) or [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Bugs**: Open a GitHub issue with reproduction steps

Thank you for contributing! 🎉
