# StyleGuard Eval Harness

**AICODE-NOTE: T008 - User-facing documentation based on quickstart.md**

Automated evaluation system for testing article generation quality. StyleGuard provides two independent CLI tools for dataset generation and quality evaluation using both numeric metrics (cosine similarity, BERTScore) and LLM-as-Judge prompts.

## Overview

StyleGuard enables objective measurement and regression tracking of article generation quality over time through:

1. **DatasetBuilder** (`prepare_dataset.py`) - Creates test datasets from text corpora by extracting neutralized topics using LLMs
2. **StyleGuard Evaluator** (`run_eval.py`) - Runs article generation on test cases and computes quality metrics

## Prerequisites

- Python 3.11+ installed
- Poetry installed (`curl -sSL https://install.python-poetry.org | python3 -`)
- OpenRouter API key (or OpenAI/Anthropic API key)
- Text corpus for testing (e.g., from Project Gutenberg)

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd eval_harness
poetry install
```

This installs all required packages:
- LLM clients (openai, anthropic)
- Metrics libraries (sentence-transformers, bert-score)
- Utilities (pyyaml, pandas, tqdm, loguru)

### 2. Configure Environment

Copy the root `.env` file or create a new one:

```bash
# Create .env if not exists
cat > .env << EOF
OPENAI_API_KEY=your_openrouter_api_key_here
MODEL=openai/gpt-4o-mini
EOF
```

**Important**: StyleGuard reuses the existing project's `.env` configuration.

### 3. Prepare Configuration Files

Copy example configs:

```bash
cp configs/dataset_config.yml my_dataset.yml
cp configs/eval_config.yml my_eval.yml
```

Edit `my_dataset.yml` to point to your corpus:

```yaml
corpus_path: "./corpus/gutenberg/"  # Update this path
output_path: "./eval_dataset/"
min_texts_per_author: 10
m_style_texts: 5
k_test_cases: 5
neutralizer_model_id: "anthropic/claude-3-5-sonnet-20240620"
max_tokens_for_neutralizer: 4000
random_seed: 42
```

Edit `my_eval.yml` to configure evaluation:

```yaml
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
```

## Quick Start (10 minutes)

### Step 1: Prepare Test Corpus

Download sample texts from Project Gutenberg or use your own:

```bash
mkdir -p corpus/mark_twain
mkdir -p corpus/charles_dickens

# Download texts (example using gutenberg CLI or wget)
# Structure: corpus/[author]/[text_file.txt]
```

**Tip**: Start with 2-3 authors and 10-12 texts each for quick testing.

### Step 2: Generate Dataset

```bash
poetry run python prepare_dataset.py --config my_dataset.yml -v
```

**Output**:
```text
Loading configuration from my_dataset.yml...
Scanning corpus at ./corpus/gutenberg/...
Found 2 authors with sufficient texts (>= 10 texts each)

Processing mark_twain: 100%|████████| 5/5 [02:15<00:00, 27.0s/case]
Processing charles_dickens: 100%|███| 5/5 [02:20<00:00, 28.0s/case]

Dataset generation complete!
  Authors processed: 2
  Total test cases: 10
  Output directory: ./eval_dataset/
```

**Time**: ~5-10 minutes for 10 test cases (depends on LLM API speed)

### Step 3: Run Evaluation

```bash
poetry run python run_eval.py --config my_eval.yml -v
```

**Output**:
```text
Loading configuration from my_eval.yml...
Loading test dataset from ./eval_dataset/...
Found 2 authors, 10 total test cases

Initializing models...
  ✓ Embedding model: all-MiniLM-L6-v2
  ✓ BERTScore: bert-base-uncased
  ✓ Generation model: meta-llama/llama-3-8b-instruct
  ✓ Judge model: openai/gpt-4o

Evaluating mark_twain: 100%|████████| 5/5 [03:45<00:00, 45.0s/case]
Evaluating charles_dickens: 100%|█| 5/5 [03:50<00:00, 46.0s/case]

Evaluation complete!
  Test cases processed: 10/10
  Mean cosine similarity: 0.823
  Mean BERTScore F1: 0.840
  Mean content score: 3.8/5.0
  Mean style score: 3.7/5.0
```

**Time**: ~10-20 minutes for 10 test cases (depends on API speed and GPU availability)

### Step 4: View Results

```bash
# View summary
cat eval_results/20251103_103045/_SUMMARY.md

# Open CSV in spreadsheet
open eval_results/20251103_103045/_SUMMARY.csv

# View specific case
cat eval_results/20251103_103045/mark_twain/case_001/generated_article.txt
```

## Common Workflows

### Testing a Single Author (Fast Iteration)

```bash
# Generate dataset (one-time)
poetry run python prepare_dataset.py --config my_dataset.yml

# Evaluate just one author (fast)
poetry run python run_eval.py --author "mark_twain" -v
```

**Time**: ~3-5 minutes for 5 test cases

### Comparing Two Model/Prompt Versions

```bash
# Run 1: Original prompt
poetry run python run_eval.py --config eval_v1.yml
# Output: eval_results/20251103_100000/

# Run 2: Updated prompt
poetry run python run_eval.py --config eval_v2.yml
# Output: eval_results/20251103_120000/

# Compare
diff eval_results/20251103_100000/_SUMMARY.csv \
     eval_results/20251103_120000/_SUMMARY.csv
```

### Debugging Dataset Generation

```bash
# Use verbose mode to see detailed logs
poetry run python prepare_dataset.py --config my_dataset.yml -v 2>&1 | tee dataset.log

# Check what went wrong
grep ERROR dataset.log
grep WARNING dataset.log
```

## Troubleshooting

### Issue: "No authors found with >= 10 texts"

**Solution**: Check your corpus structure:
```bash
# Verify directory structure
ls -R corpus/

# Should show:
# corpus/
# ├── mark_twain/
# │   ├── text_001.txt
# │   ├── text_002.txt
# │   └── ... (at least 10 files)
```

### Issue: "API authentication failed"

**Solution**: Check your `.env` file:
```bash
# Verify API key is set
cat .env | grep OPENAI_API_KEY

# Test API connectivity
poetry run python -c "import openai; print(openai.api_key)"
```

### Issue: "Out of memory" (BERTScore)

**Solution 1**: Use GPU if available:
```bash
# Check GPU
poetry run python -c "import torch; print(torch.cuda.is_available())"
```

**Solution 2**: Disable BERTScore temporarily:
```yaml
# In eval_config.yml
metrics_numeric:
  cosine_similarity: true
  bert_score: false  # Disable to save memory
```

### Issue: Evaluation is very slow

**Causes**:
- LLM API rate limits (wait between calls)
- CPU-only BERTScore computation (use GPU or disable)
- Large corpus texts (truncate in config)

**Solutions**:
```yaml
# Reduce tokens sent to neutralizer
max_tokens_for_neutralizer: 2000  # From 4000

# Increase timeout if getting timeouts
llm_timeout: 180  # From 120

# Reduce retries
max_retries: 1  # From 3
```

## Directory Structure After Setup

```text
eval_harness/
├── configs/
│   ├── dataset_config.yml        (template)
│   └── eval_config.yml            (template)
├── my_dataset.yml                 (your config)
├── my_eval.yml                    (your config)
├── corpus/                        (your texts)
│   ├── mark_twain/
│   └── charles_dickens/
├── eval_dataset/                  (generated)
│   ├── mark_twain/
│   └── charles_dickens/
└── eval_results/                  (generated)
    ├── 20251103_103045/
    └── 20251103_120000/
```

## Performance Tips

### Speed Up Dataset Generation
- Use smaller `max_tokens_for_neutralizer` (2000 instead of 4000)
- Use faster neutralizer model (e.g., gpt-4o-mini instead of claude-3-5-sonnet)
- Set `random_seed` for reproducibility (avoid regenerating same dataset)

### Speed Up Evaluation
- Disable BERTScore if memory/speed is issue
- Use faster judge model (e.g., gpt-4o-mini instead of gpt-4o)
- Use `--author` filter to test incrementally
- Use GPU for BERTScore computation

### Reduce API Costs
- Start with 2-3 authors and 3-5 test cases each
- Use cheaper models (gpt-4o-mini for judging)
- Disable judge metrics if only need numeric metrics
- Cache generation results (don't regenerate articles)

## Recommended First Run

For your first run, use these conservative settings:

```yaml
# my_dataset.yml
min_texts_per_author: 10
m_style_texts: 3        # Reduced from 5
k_test_cases: 3         # Reduced from 5
neutralizer_model_id: "openai/gpt-4o-mini"  # Cheaper
max_tokens_for_neutralizer: 2000            # Reduced

# my_eval.yml
generation_model_id: "openai/gpt-4o-mini"   # Cheaper
judge_model_id: "openai/gpt-4o-mini"        # Cheaper
metrics_numeric:
  cosine_similarity: true
  bert_score: false     # Disable for first run
metrics_judge:
  content_judge: true
  style_judge: true
```

This gives you 6 test cases (2 authors × 3 cases) in ~5-10 minutes at minimal cost.

## Next Steps

1. **Expand Corpus**: Add more authors and texts for comprehensive evaluation
2. **Experiment with Models**: Try different generation and judge models in config
3. **Tune Metrics**: Enable/disable specific metrics based on needs
4. **Automate Comparisons**: Write scripts to compare multiple evaluation runs
5. **CI/CD Integration**: Run evaluations automatically on prompt changes

## Getting Help

- **CLI Help**: `python prepare_dataset.py --help` or `python run_eval.py --help`
- **Configuration**: See [data-model.md](../specs/003-style-eval-harness/data-model.md) for full config schemas
- **Contracts**: See [contracts/](../specs/003-style-eval-harness/contracts/) for detailed CLI and prompt specifications
- **Architecture**: See [plan.md](../specs/003-style-eval-harness/plan.md) for implementation details

## Project Structure

```text
eval_harness/
├── src/
│   ├── __init__.py              # Package metadata
│   ├── dataset_builder/         # Dataset generation components
│   ├── evaluator/               # Quality evaluation components
│   └── shared/                  # Common utilities
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # End-to-end tests
│   └── fixtures/                # Test data
├── configs/                     # Example configurations
├── prepare_dataset.py           # CLI: Dataset builder
├── run_eval.py                  # CLI: Evaluator
├── pyproject.toml               # Poetry configuration
└── README.md                    # This file
```

## Development

### Running Tests

```bash
# All tests with coverage
poetry run pytest

# Specific test file
poetry run pytest tests/unit/test_builder.py -v

# Integration tests only
poetry run pytest tests/integration/ -v
```

### Code Quality

```bash
# Linting
poetry run ruff check src/

# Type checking
poetry run mypy src/

# Format code
poetry run ruff format src/
```

## License

Part of the TextScript project. See main repository for license information.
