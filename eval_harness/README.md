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
neutralizer_model_id: "anthropic/claude-3-5-sonnet-20240620"  # ⚠️ NOT IMPLEMENTED YET
max_tokens_for_neutralizer: 4000  # ⚠️ NOT IMPLEMENTED YET
random_seed: 42
```

**⚠️ Note on Neutralizer**: The topic neutralization pipeline is **not yet implemented**. Currently, `topic.json` contains generic placeholders like "Literary work 1 by Charles Dickens". See `TODO_NEUTRALIZER.md` for implementation plan to extract real neutral topics from ground truth articles.

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

**Why use author filtering**:
- Faster iteration during development
- Test prompt changes on specific writing styles
- Debug issues with particular authors
- Save API costs by testing incrementally

**Tips**:
- Author name must match directory name exactly (case-sensitive)
- Use quotes if author name has spaces: `--author "Charles Dickens"`
- Combine with other flags: `--author "mark_twain" --verbose --config custom.yml`
- Summary statistics will reflect only the filtered author's cases

### Test Modes and Prompt Versioning (NEW)

StyleGuard now supports test mode selection and prompt versioning for systematic iteration:

#### Test Mode 1: Perfect Test (Author Baseline)

Establishes author style baseline by comparing different works by the same author:

```bash
# New syntax (recommended)
poetry run python run_eval.py --test-mode perfect -v

# Legacy syntax (still works)
poetry run python run_eval.py --perfect-test -v
```

**What it does:**
- Uses `source_texts.txt` as generated output (no LLM generation)
- Compares against `ground_truth_article.txt` (both by same author)
- Measures author style consistency: expected char_ngrams ~0.99

**Expected results:**
- Char N-grams: 0.986-0.994 (same author style)
- Cosine Similarity: 0.40-0.60 (different content, same style)

#### Test Mode 2: Generation Test with Prompt Versioning

Tests actual article generation with specific prompt version:

```bash
# Use current prompt (auto-detected from metadata.yml)
poetry run python run_eval.py --test-mode generation -v

# Use specific prompt version
poetry run python run_eval.py --test-mode generation --prompt-version v1.0 -v

# Short form (generation is default mode)
poetry run python run_eval.py --prompt-version v1.0 -v
```

**Prompt versioning structure:**
```
../../TextScript/prompts/
├── article_generation.txt       # Current version
├── versions/
│   ├── v1.0.txt                 # Baseline
│   ├── v1.1.txt                 # Iteration 1
│   └── v2.0.txt                 # Major change
├── metadata.yml                  # Version tracking
└── CHANGELOG.md                  # Change history
```

#### Run Tracking and Comparison

Every test run generates metadata files:

```bash
eval_results/
├── 20251104_135314/
│   ├── _RUN_METADATA.md         # Run configuration and results
│   ├── _RUN_METADATA.json       # Programmatic access
│   ├── _SUMMARY.md
│   └── _SUMMARY.csv
└── RUNS_COMPARISON.md           # Last 20 runs comparison table
```

**View runs comparison:**
```bash
cat eval_results/RUNS_COMPARISON.md
```

**Example output:**
```markdown
| Run ID | Mode | Prompt Ver | Gen Model | Cos Sim | Char N-grams |
|--------|------|------------|-----------|---------|--------------|
| 20251104_135314 | perf | - | - | 0.527 | 0.990 |
| 20251104_120000 | gene | v1.0 | gpt-4o-mini | 0.450 | 0.850 |
```

### Comparing Two Model/Prompt Versions

```bash
# Run 1: Original prompt (v1.0)
poetry run python run_eval.py --prompt-version v1.0 -v

# Run 2: New prompt (v1.1)
poetry run python run_eval.py --prompt-version v1.1 -v

# Compare results
cat eval_results/RUNS_COMPARISON.md
# Output: eval_results/20251103_100000/

# Run 2: Updated prompt
poetry run python run_eval.py --config eval_v2.yml
# Output: eval_results/20251103_120000/

# Compare using diff (quick view)
diff eval_results/20251103_100000/_SUMMARY.csv \
     eval_results/20251103_120000/_SUMMARY.csv

# Compare using pandas (detailed analysis)
poetry run python examples/compare_runs.py \
    eval_results/20251103_100000/_SUMMARY.csv \
    eval_results/20251103_120000/_SUMMARY.csv
```

**What to look for in comparisons**:
- Mean cosine similarity: Higher = better content accuracy
- Mean BERTScore F1: Higher = better semantic matching
- Mean content score: Higher = better factual accuracy (1-5 scale)
- Mean style score: Higher = better style fidelity (1-5 scale)

**Interpreting changes**:
- Improvement: All metrics increase (e.g., +0.05 cosine, +0.5 content score)
- Regression: Any metric decreases significantly
- Trade-off: One metric improves while another degrades
- Neutral: Changes within ±0.02 for numeric, ±0.2 for judges (measurement noise)

See `examples/compare_runs.py` for automated comparison script.

### Perfect Test Mode (Baseline Calibration)

```bash
# Run perfect test to establish metric baselines
poetry run python run_eval.py --perfect-test -v
```

**What is perfect test mode?**
Perfect test mode uses the ground truth article as the "generated" output, skipping actual article generation. This establishes the upper bound of metric performance - what scores look like when generation is "perfect."

**Expected results**:
- Cosine similarity: ≥0.99 (near-perfect semantic match)
- BERTScore F1: ≥0.98 (near-perfect token alignment)
- Content score: 5/5 (perfect factual accuracy)
- Style score: 5/5 (perfect style match to itself)

**Why use perfect test mode?**
1. **Baseline calibration**: Understand what "perfect" scores look like
2. **Metric validation**: Verify metrics are working correctly
3. **Gap analysis**: Compare perfect scores vs. actual scores to measure generation quality headroom
4. **Debugging**: If perfect test doesn't produce high scores, metrics may have issues

**Example workflow**:
```bash
# Step 1: Run perfect test to get baselines
poetry run python run_eval.py --perfect-test
# Result: cosine=0.995, bert_f1=0.987, content=5.0, style=5.0

# Step 2: Run normal evaluation
poetry run python run_eval.py
# Result: cosine=0.823, bert_f1=0.840, content=3.8, style=3.7

# Step 3: Calculate quality gap
# Cosine gap: 0.995 - 0.823 = 0.172 (17.2% room for improvement)
# Content gap: 5.0 - 3.8 = 1.2 points (24% of scale)
```

**Tip**: Run perfect test after changing evaluation metrics to verify they're calibrated correctly.

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

## Common Issues

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src.ugly_script'`

**Solution**: Ensure you're in the correct directory and PYTHONPATH is set:
```bash
cd eval_harness
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
poetry run python run_eval.py
```

### Rate Limiting

**Problem**: `429 Too Many Requests - Rate limit exceeded`

**Solutions**:
1. Use `--author` flag to evaluate one author at a time
2. Switch to models with higher rate limits (e.g., gpt-4o-mini)
3. Disable some metrics to reduce API calls:
   ```yaml
   metrics_judge:
     content_judge: true
     style_judge: false  # Disable to reduce calls
   ```

### Memory Issues

**Problem**: `RuntimeError: CUDA out of memory` or `MemoryError`

**Solutions**:
1. Disable BERTScore: Set `bert_score: false` in config
2. Use GPU if available: BERTScore auto-detects CUDA
3. Evaluate fewer cases: Use `--author` filter
4. Close other applications to free memory

### Slow Performance

**Expected timing per case**:
- Dataset generation: 20-30 seconds per case
- Evaluation (with BERTScore, CPU): 40-60 seconds per case
- Evaluation (with BERTScore, GPU): 10-15 seconds per case
- Evaluation (without BERTScore): 8-12 seconds per case

**If slower than expected**:
1. Check API response times with `-v` flag
2. Disable BERTScore if not needed
3. Use faster LLM models (gpt-4o-mini instead of gpt-4o)
4. Check network connectivity to API providers

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed solutions.

## API Reference

### Dataset Builder CLI (`prepare_dataset.py`)

```bash
poetry run python prepare_dataset.py [OPTIONS]
```

**Options**:
- `--config PATH`: Path to YAML config file (default: `./configs/dataset_config.yml`)
- `-v, --verbose`: Enable verbose logging (DEBUG level)
- `-h, --help`: Show help message

**Exit Codes**:
- `0`: Success
- `1`: Configuration error (invalid config file or validation failure)
- `2`: Corpus not found (missing or empty corpus directory)
- `3`: API error (LLM authentication or rate limit issues)

**Configuration Schema** (`dataset_config.yml`):
```yaml
corpus_path: str                      # Path to text corpus (required)
output_path: str                      # Output directory (required)
min_texts_per_author: int            # Min texts per author (≥ M+K)
m_style_texts: int                   # Style reference texts (3-7)
k_test_cases: int                    # Test cases per author (3-10)
neutralizer_model_id: str            # LLM for topic neutralization
max_tokens_for_neutralizer: int      # Max tokens per neutralization (2000-8000)
random_seed: int                     # Random seed for reproducibility (optional)
```

**Example**:
```bash
# Basic usage
poetry run python prepare_dataset.py

# Custom config with verbose output
poetry run python prepare_dataset.py --config my_dataset.yml -v

# Redirect logs to file
poetry run python prepare_dataset.py -v 2>&1 | tee dataset.log
```

### Evaluator CLI (`run_eval.py`)

```bash
poetry run python run_eval.py [OPTIONS]
```

**Options**:
- `--config PATH`: Path to YAML config file (default: `./configs/eval_config.yml`)
- `--author NAME`: Evaluate specific author only (optional)
- `--perfect-test`: Use ground truth as generated output (baseline mode)
- `-v, --verbose`: Enable verbose logging (DEBUG level)
- `-h, --help`: Show help message

**Exit Codes**:
- `0`: Success
- `1`: Configuration error (invalid config file or validation failure)
- `2`: Dataset error (dataset directory not found or invalid structure)
- `3`: API error (LLM authentication or rate limit issues)
- `4`: Filesystem error (permission denied or disk full)
- `5`: Integration error (cannot import `src.ugly_script`)

**Configuration Schema** (`eval_config.yml`):
```yaml
dataset_path: str                    # Path to eval dataset (required)
output_path: str                     # Output directory (required)
generation_model_id: str             # Model for article generation
judge_model_id: str                  # Model for LLM-as-judge evaluation
embedding_model: str                 # Sentence transformer model (default: all-MiniLM-L6-v2)
llm_timeout: int                     # API timeout in seconds (default: 120)
max_retries: int                     # Max API retry attempts (default: 3)

metrics_numeric:                     # Numeric metrics configuration
  cosine_similarity: bool           # Enable cosine similarity (default: true)
  bert_score: bool                  # Enable BERTScore (default: true)

metrics_judge:                       # Judge metrics configuration
  content_judge: bool               # Enable content judge (default: true)
  style_judge: bool                 # Enable style judge (default: true)
```

**Examples**:
```bash
# Basic usage
poetry run python run_eval.py

# Evaluate specific author
poetry run python run_eval.py --author "mark_twain"

# Perfect test mode (baseline calibration)
poetry run python run_eval.py --perfect-test

# Custom config with verbose output
poetry run python run_eval.py --config my_eval.yml -v

# Multiple options
poetry run python run_eval.py --author "charles_dickens" --config fast_eval.yml -v
```

### Output Format

**Dataset Structure** (`eval_dataset/`):
```
eval_dataset/
├── [author_name]/
│   └── case_[NNN]/
│       ├── source_texts.txt          # M concatenated style texts
│       ├── ground_truth_article.txt  # Original article for comparison
│       └── topic.json                # Neutralized topic with theses
```

**Evaluation Results** (`eval_results/[TIMESTAMP]/`):
```
eval_results/20251103_103045/
├── _SUMMARY.csv                      # Per-case metrics in CSV format
├── _SUMMARY.md                       # Human-readable summary report
└── [author_name]/
    └── case_[NNN]/
        ├── generated_article.txt     # Generated article
        ├── metrics_numeric.json      # Cosine similarity + BERTScore
        ├── metrics_judge_content.json  # Content judge results
        └── metrics_judge_style.json    # Style judge results
```

**Summary CSV Columns**:
- `author`: Author name
- `case`: Case ID (case_001, case_002, ...)
- `cosine_sim`: Cosine similarity score (0.0-1.0)
- `bert_precision`: BERTScore precision (0.0-1.0)
- `bert_recall`: BERTScore recall (0.0-1.0)
- `bert_f1`: BERTScore F1 score (0.0-1.0)
- `content_score`: Content judge score (1-5)
- `style_score`: Style judge score (1-5)

**Aggregate Rows** (appended to CSV):
- `MEAN`: Mean values across all cases
- `MEDIAN`: Median values across all cases
- `STD`: Standard deviation across all cases

### Metrics Reference

**Cosine Similarity** (0.0-1.0):
- Measures semantic similarity using sentence embeddings
- **0.9-1.0**: Excellent - nearly identical content
- **0.8-0.9**: Good - strong semantic alignment
- **0.7-0.8**: Fair - moderate similarity
- **<0.7**: Poor - significant content differences

**BERTScore F1** (0.0-1.0):
- Token-level semantic similarity using BERT embeddings
- **0.9-1.0**: Excellent - high token overlap
- **0.8-0.9**: Good - strong alignment
- **0.7-0.8**: Fair - moderate alignment
- **<0.7**: Poor - weak alignment

**Content Judge** (1-5):
- LLM evaluates factual accuracy and completeness
- **5**: Perfect - all key ideas present and accurate
- **4**: Good - most ideas present with minor gaps
- **3**: Fair - notable gaps or inaccuracies
- **2**: Poor - significant missing content
- **1**: Failed - mostly unrelated or incorrect

**Style Judge** (1-5):
- LLM evaluates stylistic similarity to author
- **5**: Perfect - indistinguishable from author
- **4**: Good - recognizable author voice
- **3**: Fair - some stylistic elements present
- **2**: Poor - weak style imitation
- **1**: Failed - completely different style

### Advanced Usage

**Comparing Two Runs**:
```python
import pandas as pd

# Load two evaluation runs
df1 = pd.read_csv('eval_results/run1/_SUMMARY.csv')
df2 = pd.read_csv('eval_results/run2/_SUMMARY.csv')

# Extract mean rows
mean1 = df1[df1['author'] == 'MEAN']
mean2 = df2[df2['author'] == 'MEAN']

# Compare metrics
print(f"Cosine diff: {mean2['cosine_sim'].values[0] - mean1['cosine_sim'].values[0]:.3f}")
print(f"Content diff: {mean2['content_score'].values[0] - mean1['content_score'].values[0]:.1f}")
```

**Filtering Results**:
```python
# Load results
df = pd.read_csv('eval_results/20251103_103045/_SUMMARY.csv')

# Filter to data rows (exclude MEAN/MEDIAN/STD)
data = df[~df['author'].isin(['MEAN', 'MEDIAN', 'STD'])]

# Find best/worst cases
best = data.nlargest(5, 'content_score')
worst = data.nsmallest(5, 'content_score')
```

**Custom Metrics Analysis**:
```python
# Load individual case results
import json

with open('eval_results/.../case_001/metrics_numeric.json') as f:
    numeric = json.load(f)

print(f"Cosine: {numeric['cosine_similarity']['score']}")
print(f"BERTScore F1: {numeric['bert_score']['f1']}")

with open('eval_results/.../case_001/metrics_judge_content.json') as f:
    judge = json.load(f)

print(f"Content score: {judge['score']}")
print(f"Reasoning: {judge['reasoning']}")
```

## Performance Tips

### Optimizing for Speed
1. **Disable slow metrics**: Set `bert_score: false` (5x faster)
2. **Use faster models**: Switch to `gpt-4o-mini` for judging (2x faster)
3. **Reduce dataset size**: Start with 3 cases per author
4. **Use GPU**: BERTScore is 10x faster with CUDA
5. **Filter by author**: Test incrementally with `--author` flag

### Optimizing for Cost
1. **Use cheaper models**: `gpt-4o-mini` instead of `gpt-4o` (10x cheaper)
2. **Disable judge metrics**: Only use numeric metrics if budget is tight
3. **Smaller dataset**: Fewer test cases = fewer API calls
4. **Cache results**: Don't re-evaluate unchanged configurations
5. **Batch evaluation**: Evaluate multiple authors in one run (cheaper than separate runs)

### Optimizing for Quality
1. **Enable all metrics**: Use both numeric and judge evaluations
2. **Use best judge model**: `gpt-4o` or `claude-3-5-sonnet` for most accurate judging
3. **Larger dataset**: More cases per author (10+) for reliable statistics
4. **Multiple runs**: Run evaluation 2-3 times to check consistency
5. **Perfect test mode**: Establish baseline before real evaluation

## License

Part of the TextScript project. See main repository for license information.
