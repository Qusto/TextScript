# Changelog

All notable changes to the StyleGuard Eval Harness project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-03

### Added - Initial Release

#### Dataset Builder (`prepare_dataset.py`)
- **Automated dataset generation** from author corpus directories
- **Topic neutralization** using LLM to remove style-identifying content
- **Configurable text allocation** (M style texts, K test cases per author)
- **Reproducible splits** with random seed support
- **Multi-author support** with automatic corpus scanning
- **Validation rules** ensuring proper text allocation (M + K d min_texts)
- **Progress indicators** with tqdm for long-running operations
- **Error recovery** to continue processing other cases on failure
- **CLI interface** with `--config`, `--verbose`, and `--help` flags
- Exit codes: 0 (success), 1 (config), 2 (corpus not found), 3 (API error)

**Key Components**:
- `DatasetBuilder` class for orchestrating dataset creation
- `Neutralizer` class for LLM-based topic neutralization with retry logic
- `DatasetConfig` Pydantic model for configuration validation
- Automatic disjoint set splitting (style texts ) test texts = )

#### Evaluation Pipeline (`run_eval.py`)
- **End-to-end evaluation** of generated vs ground truth articles
- **Multiple metrics** computed in parallel:
  - Cosine similarity (sentence embeddings)
  - BERTScore (precision, recall, F1)
  - Content judge (LLM-as-judge, 1-5 score)
  - Style judge (LLM-as-judge, 1-5 score)
- **Ugly Script integration** via adapter pattern
- **Result aggregation** with mean, median, and std dev statistics
- **CSV and Markdown reports** (`_SUMMARY.csv`, `_SUMMARY.md`)
- **Timestamped output** for version tracking
- **Author filtering** via `--author` flag for partial evaluation
- **Graceful error handling** to continue evaluation on single case failure
- Exit codes: 0 (success), 1 (config), 2 (dataset not found), 3 (API), 4 (filesystem), 5 (integration)

**Key Components**:
- `EvaluationRunner` class for orchestrating evaluation
- `NumericMetrics` class for cosine similarity and BERTScore
- `JudgeEvaluator` class for LLM-as-judge content and style evaluation
- `UglyScriptAdapter` for seamless integration with article generator
- `ResultAggregator` for computing statistics and generating reports

#### Metrics & Evaluation
- **Cosine Similarity**: Sentence embedding comparison using `sentence-transformers`
- **BERTScore**: Token-level semantic similarity using BERT embeddings
- **Content Judge**: LLM evaluates semantic completeness (1-5 scale)
- **Style Judge**: LLM evaluates stylistic similarity (1-5 scale)
- **GPU auto-detection** for BERTScore (faster with CUDA)
- **Configurable metrics** - enable/disable any metric via config
- **Min text length validation** (50+ chars for embeddings, 100+ for judges)

#### Configuration & Validation
- **Pydantic V2 models** for type-safe configuration
- **YAML configuration files** with validation
- **Environment variable support** via `.env` file
- **Comprehensive validation rules**:
  - Text allocation: M + K d min_texts_per_author
  - Score bounds: cosine/BERT  [0,1], judge  [1,5]
  - Reasoning length: 50-500 characters for judge
  - Theses count: 3-7 per topic
- **Default values** for all optional parameters

#### CLI Interface
- **Argparse-based** command-line interfaces
- **Help messages** with detailed usage information
- **Verbose mode** (`-v`/`--verbose`) for detailed logging
- **Config file override** (`--config PATH`) for custom configurations
- **Author filtering** (`--author NAME`) for partial evaluation
- **Exit codes** following UNIX conventions

#### Testing & Quality
- **168 tests** covering unit and integration scenarios
- **pytest-based** testing framework
- **Mocked LLM calls** for deterministic testing
- **Test fixtures** for reusable test data
- **Parametrized tests** for comprehensive coverage
- **AICODE comments** documenting design decisions
- **TDD methodology** throughout development

#### Documentation
- **README.md**: Project overview and quick start
- **quickstart.md**: Step-by-step tutorial
- **TROUBLESHOOTING.md**: Common issues and solutions
- **CONTRIBUTING.md**: Development guidelines
- **data-model.md**: Configuration reference
- **cli-dataset.md**: Dataset CLI specification
- **cli-evaluator.md**: Evaluator CLI specification
- **prompts.md**: Judge prompt templates

#### Infrastructure
- **Poetry** for dependency management (Python 3.11+)
- **Loguru** for structured, colorized logging
- **python-dotenv** for environment variable management
- **sentence-transformers** for embedding models
- **bert-score** for semantic similarity
- **PyYAML** for configuration parsing
- **tqdm** for progress bars

### Performance Characteristics
- **Dataset generation**: ~2-3 min per case (dependent on LLM API)
- **Evaluation**: ~10-15 sec per case (with BERTScore on CPU)
- **GPU acceleration**: 5x faster BERTScore with CUDA
- **Memory usage**: 2-4GB RAM (4-8GB with BERTScore)
- **Disk usage**: ~100-500MB per full evaluation run

### Known Limitations
- **Ugly Script dependency**: Requires `src.ugly_script` module from main repository
- **LLM API required**: Cannot run without API keys (OpenAI/Anthropic/OpenRouter)
- **BERT Score memory**: High memory usage on CPU, may require GPU for large evaluations
- **Sequential processing**: Cases evaluated sequentially (no parallelization)
- **English only**: Designed for English text evaluation

### Migration Notes
This is the initial release. No migration required.

### Dependencies
See `pyproject.toml` for complete dependency list. Key dependencies:
- Python e 3.11
- pydantic e 2.0
- torch e 2.0
- sentence-transformers e 2.2
- bert-score e 0.3
- loguru e 0.7
- pyyaml e 6.0
- python-dotenv e 1.0
- tqdm e 4.60

### Contributors
- StyleGuard Team
- Initial development following TDD methodology
- Comprehensive AICODE documentation

### Links
- **Repository**: https://github.com/your-org/TextScript
- **Issues**: https://github.com/your-org/TextScript/issues
- **Documentation**: See `docs/` directory
- **Specification**: See `specs/003-style-eval-harness/`

---

## [Unreleased]

### Planned Features
- Parallel case evaluation for faster processing
- Caching for topic neutralization to avoid duplicate LLM calls
- Additional metrics (ROUGE, BLEU, perplexity)
- Interactive CLI prompts for configuration
- Web dashboard for visualization
- Multi-language support beyond English
- Automatic hyperparameter tuning

### Under Consideration
- Integration with MLflow for experiment tracking
- Docker containerization for reproducible environments
- CI/CD pipeline for automated testing
- Benchmark datasets with published results
- Fine-tuned embedding models for literary style

---

## Version History

### How to Read Version Numbers
Given a version number MAJOR.MINOR.PATCH:
- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

### Changelog Format
Each version documents:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be-removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

---

**Note**: This changelog is manually maintained. Please update when making releases.
