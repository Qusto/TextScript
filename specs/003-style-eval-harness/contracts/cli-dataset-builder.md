# CLI Contract: Dataset Builder

**Command**: `prepare_dataset.py`
**Purpose**: Generate evaluation dataset from text corpus
**Component**: Dataset Builder (Component A)

## Command Signature

```bash
python prepare_dataset.py [OPTIONS]
```

## Options

### `--config PATH`
- **Type**: File path
- **Default**: `./configs/dataset_config.yml`
- **Required**: No
- **Description**: Path to YAML configuration file
- **Example**: `--config my_config.yml`

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

- `0`: Success - dataset generated without errors
- `1`: Configuration error (invalid config file, missing required fields)
- `2`: Input error (corpus not found, insufficient texts per author)
- `3`: LLM API error (authentication failed, quota exceeded)
- `4`: File system error (cannot write to output directory)

## Standard Output

### Normal Mode

```text
Loading configuration from ./configs/dataset_config.yml...
Scanning corpus at ./corpus/gutenberg/...
Found 5 authors with sufficient texts (>= 10 texts each)

Processing mark_twain...
  Splitting 15 texts: 5 for style, 5 for test cases
  Generating case_001... ✓
  Generating case_002... ✓
  Generating case_003... ✓
  Generating case_004... ✓
  Generating case_005... ✓

Processing charles_dickens...
  [similar output]

Dataset generation complete!
  Authors processed: 5
  Total test cases: 25
  Output directory: ./eval_dataset/
```

### Verbose Mode (`-v`)

Adds detailed logging:
```text
[2025-11-03 10:15:30] INFO: Loading configuration from ./configs/dataset_config.yml
[2025-11-03 10:15:30] DEBUG: Config: corpus_path=./corpus/gutenberg/, min_texts=10
[2025-11-03 10:15:31] INFO: Scanning corpus at ./corpus/gutenberg/
[2025-11-03 10:15:31] DEBUG: Found author: mark_twain (15 texts)
[2025-11-03 10:15:31] DEBUG: Found author: charles_dickens (12 texts)
[2025-11-03 10:15:31] INFO: Found 5 authors with sufficient texts
[2025-11-03 10:15:32] INFO: Processing mark_twain
[2025-11-03 10:15:32] DEBUG: Random split (seed=42): style=[0,3,7,11,14], test=[1,2,4,5,6]
[2025-11-03 10:15:32] INFO: Generating case_001
[2025-11-03 10:15:32] DEBUG: Combining 5 style texts (total: 45KB)
[2025-11-03 10:15:33] DEBUG: Calling neutralizer API with 3500 tokens
[2025-11-03 10:15:37] DEBUG: Received topic: "Adventures on Mississippi River"
[2025-11-03 10:15:37] INFO: Case case_001 complete
[... similar detailed logs ...]
```

## Standard Error

### Error Messages

```text
# Configuration error
ERROR: Configuration file not found: ./configs/dataset_config.yml
ERROR: Invalid config: m_style_texts (5) + k_test_cases (8) > min_texts_per_author (10)

# Input error
ERROR: Corpus directory not found: ./corpus/gutenberg/
ERROR: No authors found with >= 10 texts in corpus
WARNING: Skipping author 'jane_austen': only 7 texts found (minimum: 10)

# LLM API error
ERROR: Failed to neutralize ./corpus/mark_twain/text_001.txt: API authentication failed
ERROR: Neutralizer API timeout after 120s (case_003, retry 2/3)
WARNING: Rate limit hit, waiting 60s before retry...

# File system error
ERROR: Cannot write to output directory: ./eval_dataset/ (permission denied)
ERROR: Failed to save topic.json: disk full
```

## Configuration File Format

See [data-model.md](../data-model.md#dataset_configyml) for complete schema.

**Example**:
```yaml
corpus_path: "./corpus/gutenberg/"
output_path: "./eval_dataset/"
min_texts_per_author: 10
m_style_texts: 5
k_test_cases: 5
neutralizer_model_id: "anthropic/claude-3-5-sonnet-20240620"
max_tokens_for_neutralizer: 4000
random_seed: 42
```

## Output Structure

Creates directory structure in `output_path`:

```text
eval_dataset/
├── [author_1]/
│   ├── case_001/
│   │   ├── source_texts.txt
│   │   ├── ground_truth_article.txt
│   │   └── topic.json
│   ├── case_002/
│   │   └── ...
│   └── case_NNN/
└── [author_2]/
    └── ...
```

See [data-model.md](../data-model.md#output-evaluation-dataset) for file format details.

## Progress Indicators

Uses `tqdm` progress bars for long operations:

```text
Processing mark_twain: 100%|████████████████| 5/5 [01:23<00:00, 16.7s/case]
Processing charles_dickens: 40%|██████      | 2/5 [00:35<00:52, 17.5s/case]
```

## Environment Variables

Requires `.env` file in repository root with:

```bash
OPENAI_API_KEY=your_openrouter_api_key_here
```

The `neutralizer_model_id` from config uses this API key for authentication.

## Examples

### Basic usage with default config
```bash
python prepare_dataset.py
```

### Custom config file
```bash
python prepare_dataset.py --config my_dataset_config.yml
```

### Verbose mode for debugging
```bash
python prepare_dataset.py -v
```

### Custom config with verbose output
```bash
python prepare_dataset.py --config custom.yml -v 2>&1 | tee dataset_build.log
```

## Idempotency

Running the command multiple times with same configuration and `random_seed`:
- **Same random_seed**: Produces identical dataset (same text splits)
- **No random_seed**: Different random splits each run
- **Existing output**: Overwrites existing files (no merge or skip logic)

**Recommendation**: Use `random_seed` for reproducible datasets.

## Performance

Typical execution times (excluding LLM API latency):

- Corpus scanning: <5s for 1000 files
- File I/O: ~1s per test case
- LLM neutralization: 3-10s per test case (depends on API)

**Total time** for 5 authors × 5 cases = 25 cases:
- Best case: ~2 minutes (fast API responses)
- Typical: ~10-15 minutes
- Worst case: ~30 minutes (slow API, retries)

## Error Recovery

- **Single case failure**: Logs error, continues to next case
- **Author failure**: Logs error, continues to next author
- **Critical failure** (config error, corpus missing): Exits immediately with error code

Partial datasets are valid - missing cases can be regenerated by running again.

## Validation

The script validates:
1. Configuration file syntax and values
2. Corpus directory existence and structure
3. Author text count requirements
4. LLM API responses (JSON structure)
5. Output directory write permissions

All validation errors are reported before starting generation.
