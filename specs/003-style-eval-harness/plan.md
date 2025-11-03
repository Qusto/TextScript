# Implementation Plan: StyleGuard - Eval Harness

**Branch**: `003-style-eval-harness` | **Date**: 2025-11-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-style-eval-harness/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

StyleGuard is an automated evaluation harness for testing the quality of the article generation system. It consists of two independent CLI tools: (1) DatasetBuilder that creates test datasets from text corpora by extracting neutralized topics using LLMs, and (2) StyleGuard evaluator that runs article generation on test cases and computes quality metrics using both numeric methods (cosine similarity, BERTScore) and LLM-as-Judge prompts for content accuracy and style fidelity. The system enables objective measurement and regression tracking of article generation quality over time.

## Technical Context

**Language/Version**: Python 3.11+ (matching existing backend stack)
**Primary Dependencies**:
- Poetry for dependency management (existing project standard)
- openai/anthropic SDK for LLM API calls (reuse existing .env OPENAI_API_KEY)
- PyYAML for configuration files
- sentence-transformers for embedding-based similarity
- bert-score for semantic similarity metrics
- pandas for aggregating and reporting metrics
- tqdm for progress indicators
- loguru for structured logging (existing backend dependency)

**Storage**: File-based (eval_dataset/, eval_results/ directories with structured JSON and text files)
**Testing**: pytest with pytest-asyncio (existing backend test framework)
**Target Platform**: Local development environment (macOS/Linux) with CLI access
**Project Type**: Single project (CLI tools extending existing Python codebase)
**Performance Goals**:
- Dataset generation: Process 5 authors × 10 texts in <30 min (excluding LLM latency)
- Evaluation: Process 25 test cases with all metrics in <60 min (excluding LLM latency)

**Constraints**:
- Must integrate with existing Ugly Script as importable module
- Must reuse existing .env configuration (OPENAI_API_KEY, MODEL variables)
- Must be runnable independently from web frontend/backend services
- All LLM API calls must handle timeouts/retries gracefully

**Special Features**:
- Perfect test mode (--perfect-test flag): Uses ground truth article as generated output to establish baseline metrics (expected: cosine≈1.0, BERTScore≈1.0, judges=5/5)
- Enables metric calibration and upper-bound understanding without generation cost

**Scale/Scope**:
- Initial scope: 5-10 authors, 5-10 test cases per author
- Dataset size: ~50-100 test cases total
- Metric outputs: ~400-500 JSON files per evaluation run (4 metrics × 100 cases)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file is currently a template placeholder. Applying general best practices for Python CLI tools:

✅ **Library-First Principle**: Both components (DatasetBuilder and Evaluator) will be structured as importable Python modules with CLI entry points
✅ **Test-First Development**: TDD approach with pytest - tests written before implementation
✅ **CLI Interface**: Standard CLI with argparse, stdin/stdout protocol, JSON + human-readable output
✅ **Observability**: Structured logging with loguru, progress indicators with tqdm
✅ **Simplicity**: File-based storage, YAML configs, no additional databases or services required

**Potential Violations**: None identified. Feature aligns with existing project structure and conventions.

## Project Structure

### Documentation (this feature)

```text
specs/003-style-eval-harness/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - technology decisions and patterns
├── data-model.md        # Phase 1 output - file formats and data structures
├── quickstart.md        # Phase 1 output - setup and usage guide
├── contracts/           # Phase 1 output - CLI interfaces and prompts
│   ├── cli-dataset-builder.md
│   ├── cli-evaluator.md
│   ├── prompt-neutralizer.md
│   ├── prompt-content-judge.md
│   └── prompt-style-judge.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
eval_harness/                    # New directory for evaluation system
├── src/
│   ├── __init__.py
│   ├── dataset_builder/        # Component A: Dataset generation
│   │   ├── __init__.py
│   │   ├── builder.py          # Main dataset builder logic
│   │   ├── neutralizer.py      # LLM-based topic neutralization
│   │   └── config.py           # Configuration models (Pydantic)
│   ├── evaluator/              # Component B: Quality evaluation
│   │   ├── __init__.py
│   │   ├── runner.py           # Main evaluation runner
│   │   ├── metrics/            # Metric computation modules
│   │   │   ├── __init__.py
│   │   │   ├── numeric.py      # Cosine similarity, BERTScore
│   │   │   └── judge.py        # LLM-as-Judge evaluation
│   │   ├── integration.py      # Integration with Ugly Script
│   │   └── config.py           # Configuration models (Pydantic)
│   └── shared/                 # Shared utilities
│       ├── __init__.py
│       ├── llm_client.py       # Unified LLM API client (reuse .env)
│       └── file_utils.py       # File I/O helpers
├── tests/
│   ├── unit/
│   │   ├── test_builder.py
│   │   ├── test_neutralizer.py
│   │   ├── test_metrics.py
│   │   └── test_integration.py
│   ├── integration/
│   │   ├── test_dataset_pipeline.py
│   │   └── test_eval_pipeline.py
│   └── fixtures/               # Test data
│       ├── sample_corpus/
│       └── sample_dataset/
├── configs/                    # Example configuration files
│   ├── dataset_config.yml
│   └── eval_config.yml
├── prepare_dataset.py          # CLI entry point for dataset builder
├── run_eval.py                 # CLI entry point for evaluator
├── pyproject.toml              # Poetry configuration
└── README.md                   # Setup and usage documentation

# Generated artifacts (gitignored)
corpus/                          # User-provided text corpus
eval_dataset/                    # Generated test datasets
eval_results/                    # Evaluation outputs
```

**Structure Decision**: Standalone project in `eval_harness/` directory at repository root. This keeps the evaluation system independent from the web application (backend/frontend) and original script (src/), while allowing it to import and use the article generation functionality as a library. Uses Poetry for dependency management to match existing backend conventions.
