# CLI Contract: Evaluator

**Command**: `run_eval.py`
**Purpose**: Run article generation and compute quality metrics
**Component**: StyleGuard Evaluator (Component B)

## Command Signature

```bash
python run_eval.py [OPTIONS]
```

## Options

### `--config PATH`
- **Type**: File path
- **Default**: `./configs/eval_config.yml`
- **Required**: No
- **Description**: Path to YAML configuration file
- **Example**: `--config my_eval_config.yml`

### `--author NAME`
- **Type**: String
- **Default**: None (process all authors)
- **Required**: No
- **Description**: Filter evaluation to specific author's test cases only
- **Example**: `--author "mark_twain"`

### `--perfect-test`
- **Type**: Flag
- **Default**: False
- **Required**: No
- **Description**: Enable perfect test mode - use ground truth article as generated output for baseline metric calibration
- **Example**: `--perfect-test`
- **Expected Results**: Cosine similarity ≥0.99, BERTScore F1 ≥0.98, Content/Style scores = 5/5

### `--verbose` / `-v`
- **Type**: Flag
- **Default**: False
- **Required**: No
- **Description**: Enable verbose logging output
- **Example**: `-v`

### `--help` / `-h`
- **Type**: Flag
- **Description**: Show help message and exit

## Exit Codes

- `0`: Success - evaluation completed without critical errors
- `1`: Configuration error (invalid config file, missing required fields)
- `2`: Input error (dataset not found, invalid dataset structure)
- `3`: LLM API error (authentication failed, quota exceeded - all cases failed)
- `4`: File system error (cannot write to output directory)
- `5`: Integration error (cannot import or call Ugly Script functions)

## Standard Output

### Normal Mode

```text
Loading configuration from ./configs/eval_config.yml...
Loading test dataset from ./eval_dataset/...
Found 5 authors, 25 total test cases

Initializing models...
  ✓ Embedding model: all-MiniLM-L6-v2
  ✓ BERTScore: bert-base-uncased
  ✓ Generation model: meta-llama/llama-3-8b-instruct
  ✓ Judge model: openai/gpt-4o

Running evaluation...
Evaluating mark_twain: 100%|████████████| 5/5 [02:15<00:00, 27.0s/case]
Evaluating charles_dickens: 100%|█████████| 5/5 [02:20<00:00, 28.0s/case]
[... other authors ...]

Generating summary report...
✓ Saved detailed results to ./eval_results/20251103_103045/
✓ Saved summary to ./eval_results/20251103_103045/_SUMMARY.csv

Evaluation complete!
  Test cases processed: 25/25
  Mean cosine similarity: 0.823
  Mean BERTScore F1: 0.840
  Mean content score: 3.8/5.0
  Mean style score: 3.7/5.0
```

### Verbose Mode (`-v`)

Adds detailed logging:
```text
[2025-11-03 10:30:15] INFO: Loading configuration from ./configs/eval_config.yml
[2025-11-03 10:30:15] DEBUG: Config: dataset_path=./eval_dataset/, generation_model=meta-llama/llama-3-8b-instruct
[2025-11-03 10:30:16] INFO: Loading test dataset from ./eval_dataset/
[2025-11-03 10:30:16] DEBUG: Found author: mark_twain (5 cases)
[2025-11-03 10:30:16] DEBUG: Found author: charles_dickens (5 cases)
[2025-11-03 10:30:16] INFO: Found 5 authors, 25 total test cases
[2025-11-03 10:30:17] INFO: Initializing embedding model: all-MiniLM-L6-v2
[2025-11-03 10:30:18] DEBUG: Model loaded, device: cpu
[2025-11-03 10:30:18] INFO: Starting evaluation run (ID: 20251103_103045)
[2025-11-03 10:30:19] INFO: Processing mark_twain/case_001
[2025-11-03 10:30:19] DEBUG: Loading source_texts.txt (45KB)
[2025-11-03 10:30:19] DEBUG: Loading topic.json: "Adventures on Mississippi River"
[2025-11-03 10:30:20] DEBUG: Analyzing style with Ugly Script...
[2025-11-03 10:30:35] DEBUG: Generating article with style profile...
[2025-11-03 10:30:52] INFO: Article generated (8.5KB)
[2025-11-03 10:30:52] DEBUG: Computing cosine similarity...
[2025-11-03 10:30:53] DEBUG: Cosine similarity: 0.85
[2025-11-03 10:30:53] DEBUG: Computing BERTScore...
[2025-11-03 10:30:56] DEBUG: BERTScore F1: 0.87
[2025-11-03 10:30:56] DEBUG: Calling content judge API...
[2025-11-03 10:31:01] DEBUG: Content score: 4/5
[2025-11-03 10:31:01] DEBUG: Calling style judge API...
[2025-11-03 10:31:06] DEBUG: Style score: 3/5
[2025-11-03 10:31:06] INFO: Case mark_twain/case_001 complete
[... similar detailed logs for each case ...]
```

### Author Filter Mode

```text
# Using --author filter
python run_eval.py --author "mark_twain"

Loading configuration from ./configs/eval_config.yml...
Loading test dataset from ./eval_dataset/...
Filtering by author: mark_twain
Found 1 author, 5 test cases

[... evaluation continues for only mark_twain cases ...]

Evaluation complete!
  Test cases processed: 5/5
  Mean cosine similarity: 0.842 (mark_twain only)
  Mean BERTScore F1: 0.856 (mark_twain only)
  Mean content score: 4.0/5.0 (mark_twain only)
  Mean style score: 3.6/5.0 (mark_twain only)
```

### Perfect Test Mode

```text
# Using --perfect-test for baseline calibration
python run_eval.py --perfect-test

Loading configuration from ./configs/eval_config.yml...
Loading test dataset from ./eval_dataset/...
Found 5 authors, 25 total test cases

⚠️ PERFECT TEST MODE ENABLED - Using ground truth as generated output

Initializing models...
  ✓ Embedding model: all-MiniLM-L6-v2
  ✓ BERTScore: bert-base-uncased
  ✓ Judge model: openai/gpt-4o
  ⚠️ Generation model: SKIPPED (perfect test mode)

Running evaluation...
Evaluating mark_twain: 100%|████████████| 5/5 [00:45<00:00, 9.0s/case]
Evaluating charles_dickens: 100%|█████████| 5/5 [00:48<00:00, 9.6s/case]
[... other authors ...]

Evaluation complete!
  Test cases processed: 25/25
  Mean cosine similarity: 0.995 ✓ (BASELINE)
  Mean BERTScore F1: 0.987 ✓ (BASELINE)
  Mean content score: 5.0/5.0 ✓ (BASELINE)
  Mean style score: 5.0/5.0 ✓ (BASELINE)

✓ Perfect test mode validation passed - metrics are properly calibrated
```

**Use Case**: Run perfect test to establish upper bound for metric interpretation. Compare with normal evaluation results to measure generation quality gap.

## Standard Error

### Error Messages

```text
# Configuration error
ERROR: Configuration file not found: ./configs/eval_config.yml
ERROR: Invalid config: at least one metric must be enabled

# Input error
ERROR: Dataset directory not found: ./eval_dataset/
ERROR: Invalid dataset structure: missing topic.json in case_001
WARNING: Skipping case mark_twain/case_003: ground_truth_article.txt is empty

# LLM API error
ERROR: Failed to generate article for case_001: API authentication failed
WARNING: Content judge evaluation failed for case_002 (retry 3/3): timeout
ERROR: All test cases failed due to API errors - check credentials

# Integration error
ERROR: Cannot import ugly_script: module not found
ERROR: ugly_script.analyze_style() failed: unexpected argument format

# Metric computation error
WARNING: BERTScore failed for case_004: texts too short
WARNING: Cosine similarity undefined for case_005: empty generated article
```

## Configuration File Format

See [data-model.md](../data-model.md#eval_configyml) for complete schema.

**Example**:
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
embedding_model: "all-MiniLM-L6-v2"
llm_timeout: 120
max_retries: 3
```

## Output Structure

Creates timestamped directory in `output_path`:

```text
eval_results/
└── 20251103_103045/              # Timestamp: YYYYMMDD_HHMMSS
    ├── mark_twain/
    │   ├── case_001/
    │   │   ├── generated_article.txt
    │   │   ├── metrics_numeric.json
    │   │   ├── metrics_judge_content.json
    │   │   └── metrics_judge_style.json
    │   └── case_NNN/
    ├── charles_dickens/
    │   └── ...
    ├── _SUMMARY.csv              # Aggregated metrics (all cases)
    └── _SUMMARY.md               # Human-readable report
```

See [data-model.md](../data-model.md#output-evaluation-results) for file format details.

## Progress Indicators

Uses `tqdm` progress bars showing per-author progress:

```text
Evaluating mark_twain: 100%|██████████████| 5/5 [02:15<00:00, 27.0s/case]
Evaluating charles_dickens: 60%|████████  | 3/5 [01:25<00:55, 28.0s/case]
```

## Environment Variables

Requires `.env` file in repository root with:

```bash
OPENAI_API_KEY=your_openrouter_api_key_here
```

Both `generation_model_id` and `judge_model_id` from config use this API key.

## Examples

### Basic usage with default config
```bash
python run_eval.py
```

### Custom config file
```bash
python run_eval.py --config my_eval_config.yml
```

### Evaluate specific author only
```bash
python run_eval.py --author "mark_twain"
```

### Verbose mode for debugging
```bash
python run_eval.py -v
```

### Perfect test mode for baseline calibration
```bash
python run_eval.py --perfect-test
```

### Combined options
```bash
python run_eval.py --config custom.yml --author "dickens" -v
```

### Save logs to file
```bash
python run_eval.py -v 2>&1 | tee eval_run.log
```

## Idempotency

Running the command multiple times:
- **Different timestamps**: Each run creates new output directory (no overwrite)
- **Same dataset**: Can run evaluation multiple times on same dataset
- **Different configs**: Can compare results from different model/metric configurations

**Recommendation**: Keep all evaluation runs for comparison over time.

## Performance

Typical execution times per test case:

- Load test case files: ~0.5s
- Style analysis (Ugly Script): ~10-20s (depends on LLM API)
- Article generation (Ugly Script): ~15-25s (depends on LLM API)
- Cosine similarity: ~0.5s
- BERTScore: ~2-5s (CPU) or ~0.5s (GPU)
- Content judge (LLM): ~3-8s (depends on API)
- Style judge (LLM): ~3-8s (depends on API)

**Total time per case**: ~35-70s (depending on API latency and CPU/GPU)

**Total time** for 25 test cases:
- Best case: ~15 minutes (fast APIs, GPU for BERTScore)
- Typical: ~30-45 minutes
- Worst case: ~60-90 minutes (slow APIs, CPU only, retries)

## Error Recovery

- **Single metric failure**: Logs warning, continues with other metrics
- **Single case failure**: Logs error, continues to next case
- **Author failure**: Logs error, continues to next author
- **Critical failure** (config error, dataset missing, no API key): Exits immediately

Partial results are saved - failed cases show `null` values in summary CSV.

## Graceful Degradation

When optional metrics fail:
```text
WARNING: BERTScore computation failed: out of memory
INFO: Continuing with remaining metrics (cosine_similarity, judges)

# In _SUMMARY.csv, bert_f1 column will have null/empty values
```

Evaluation continues as long as at least one metric succeeds.

## Validation

The script validates:
1. Configuration file syntax and values
2. Dataset directory existence and structure
3. Required files present in each test case
4. Model availability (embedding model download)
5. LLM API connectivity (test call before starting)
6. Ugly Script integration (import and function availability)

All validation errors are reported before starting evaluation.

## Comparison Workflow

To compare two evaluation runs:

```bash
# Run 1: Original prompt
python run_eval.py --config config_v1.yml
# Output: eval_results/20251103_103045/

# Run 2: Updated prompt
python run_eval.py --config config_v2.yml
# Output: eval_results/20251103_110230/

# Compare summaries
diff eval_results/20251103_103045/_SUMMARY.csv \
     eval_results/20251103_110230/_SUMMARY.csv
```

Or use pandas to load and compare CSVs programmatically.
