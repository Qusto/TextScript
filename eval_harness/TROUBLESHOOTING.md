# Troubleshooting Guide: StyleGuard Eval Harness

**AICODE-NOTE: T124 - Common issues and solutions for users**

This guide helps you diagnose and fix common problems when using StyleGuard.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Errors](#configuration-errors)
- [Dataset Generation Problems](#dataset-generation-problems)
- [Evaluation Failures](#evaluation-failures)
- [API Issues](#api-issues)
- [Memory and Performance](#memory-and-performance)
- [Integration Errors](#integration-errors)

---

## Installation Issues

### Issue: Poetry install fails with dependency conflicts

**Symptoms**:
```bash
poetry install
# Error: Could not find a version that satisfies the requirement...
```

**Solutions**:

1. Update Poetry to latest version:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Clear Poetry cache and reinstall:
   ```bash
   poetry cache clear --all pypi
   poetry install
   ```

3. Check Python version (must be 3.11+):
   ```bash
   python --version
   # Should show Python 3.11.x or higher
   ```

4. If using pyenv, ensure Python 3.11+ is active:
   ```bash
   pyenv local 3.11.0
   poetry env use python3.11
   poetry install
   ```

### Issue: torch (PyTorch) installation fails

**Symptoms**:
```bash
ERROR: Could not install packages due to an OSError:
  [Errno 28] No space left on device
```

**Solutions**:

1. Free up disk space (PyTorch is large, ~2-3GB)

2. Install CPU-only PyTorch first (smaller):
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   poetry install
   ```

3. For Apple Silicon Macs, use MPS-enabled PyTorch:
   ```bash
   poetry add torch --platform darwin --python "^3.11"
   ```

---

## Configuration Errors

### Issue: "OPENAI_API_KEY not found in environment"

**Exit Code**: 3 (API error)

**Symptoms**:
```bash
poetry run python prepare_dataset.py
# ERROR: OPENAI_API_KEY not found in environment
```

**Solutions**:

1. Create `.env` file in repository root (not in eval_harness/):
   ```bash
   cd /path/to/TextScript  # Repository root
   cat > .env << EOF
   OPENAI_API_KEY=sk-or-v1-your-actual-key-here
   MODEL=openai/gpt-4o-mini
   EOF
   ```

2. Verify `.env` file location:
   ```bash
   # Should be at repository root, not in eval_harness/
   ls -la .env
   ```

3. Test API key is loaded:
   ```bash
   cd eval_harness
   poetry run python -c "import os; from dotenv import load_dotenv; load_dotenv('../.env'); print(os.getenv('OPENAI_API_KEY'))"
   ```

### Issue: "Configuration validation failed: min_texts_per_author"

**Exit Code**: 1 (Configuration error)

**Symptoms**:
```bash
poetry run python prepare_dataset.py --config my_config.yml
# ERROR: Configuration validation failed: m_style_texts + k_test_cases (10) exceeds min_texts_per_author (10)
```

**Solution**:

The validation rule is: `m_style_texts + k_test_cases <= min_texts_per_author`

Fix your config:
```yaml
# Option 1: Increase min_texts_per_author
min_texts_per_author: 12  # Was 10

# Option 2: Reduce m_style_texts or k_test_cases
m_style_texts: 4  # Was 5
k_test_cases: 4   # Was 5
```

**Why this rule exists**: We need to split texts into style examples (M) and test cases (K) without overlap.

---

## Dataset Generation Problems

### Issue: "No authors found with >= 10 texts"

**Exit Code**: 2 (Input error)

**Symptoms**:
```bash
poetry run python prepare_dataset.py
# ERROR: No authors found with >= 10 texts in corpus
```

**Solutions**:

1. Verify corpus directory structure:
   ```bash
   ls -R corpus/
   # Expected structure:
   # corpus/
   # ├── mark_twain/
   # │   ├── text_001.txt
   # │   ├── text_002.txt
   # │   └── ... (at least 10 files)
   # └── charles_dickens/
   #     └── ... (at least 10 files)
   ```

2. Check file permissions:
   ```bash
   # All text files should be readable
   find corpus/ -name "*.txt" -ls
   ```

3. Reduce `min_texts_per_author` in config (temporary workaround):
   ```yaml
   min_texts_per_author: 5  # Reduced from 10
   m_style_texts: 2
   k_test_cases: 2
   ```

4. Download more texts from Project Gutenberg:
   ```bash
   # Example: Download Mark Twain works
   wget -P corpus/mark_twain/ https://www.gutenberg.org/cache/epub/74/pg74.txt
   wget -P corpus/mark_twain/ https://www.gutenberg.org/cache/epub/76/pg76.txt
   # ... repeat for at least 10 texts
   ```

### Issue: Dataset generation is very slow (>5 min per case)

**Symptoms**:
```bash
Processing mark_twain: 1/5 [00:05<00:20, 5min/case]
```

**Solutions**:

1. Use faster neutralizer model:
   ```yaml
   # In dataset_config.yml
   neutralizer_model_id: "openai/gpt-4o-mini"  # Fast and cheap
   # Instead of: "anthropic/claude-3-5-sonnet-20240620"
   ```

2. Reduce token limit:
   ```yaml
   max_tokens_for_neutralizer: 2000  # From 4000
   ```

3. Check API rate limits:
   - OpenRouter: Check dashboard at https://openrouter.ai/
   - Look for 429 errors in logs with `-v` flag

4. Use verbose mode to identify bottleneck:
   ```bash
   poetry run python prepare_dataset.py -v 2>&1 | tee dataset.log
   grep "took" dataset.log  # Shows timing for each step
   ```

### Issue: Neutralizer returns malformed JSON

**Symptoms**:
```bash
WARNING: Neutralizer failed for case_003: Invalid JSON in LLM response
```

**Solutions**:

1. This is usually handled automatically (retry with format reminder)

2. Check if specific model has issues:
   ```yaml
   # Try more reliable model
   neutralizer_model_id: "openai/gpt-4o"  # Better at JSON
   ```

3. Enable verbose logging to see raw responses:
   ```bash
   poetry run python prepare_dataset.py -v
   ```

4. If many cases fail, check if model supports JSON output:
   - GPT-4o: Yes (use `response_format={"type": "json_object"}`)
   - Claude 3.5 Sonnet: Yes (good JSON)
   - Llama models: Variable (some struggle with JSON)

---

## Evaluation Failures

### Issue: "Dataset directory not found"

**Exit Code**: 2 (Dataset error)

**Symptoms**:
```bash
poetry run python run_eval.py
# ERROR: Dataset directory not found: ./eval_dataset/
```

**Solutions**:

1. Generate dataset first:
   ```bash
   poetry run python prepare_dataset.py
   ```

2. Specify correct dataset path:
   ```bash
   poetry run python run_eval.py --config my_config.yml
   ```

   Where `my_config.yml` contains:
   ```yaml
   dataset_path: "/absolute/path/to/eval_dataset/"
   ```

3. Check dataset structure:
   ```bash
   ls -R eval_dataset/
   # Should show author/case_NNN/ subdirectories
   ```

### Issue: "Integration error: cannot import ugly_script"

**Exit Code**: 5 (Integration error)

**Symptoms**:
```bash
poetry run python run_eval.py
# ERROR: Integration error: cannot import module 'src.ugly_script'
```

**Solutions**:

1. Ensure you're in the eval_harness directory:
   ```bash
   cd eval_harness
   poetry run python run_eval.py
   ```

2. Check if Ugly Script exists:
   ```bash
   ls -la ../src/ugly_script.py
   # Should exist at repository root
   ```

3. Add repository root to PYTHONPATH:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/TextScript"
   poetry run python run_eval.py
   ```

4. If Ugly Script is missing, this feature depends on 001-style-article-generator:
   - Ensure you've implemented that feature first
   - Or create mock implementation for testing

### Issue: All test cases fail during evaluation

**Symptoms**:
```bash
Evaluating mark_twain: 0/5 [00:00<?, ?/s]
ERROR: Evaluation failed
Test cases processed: 0/5
```

**Solutions**:

1. Check API authentication:
   ```bash
   # Verify API key works
   poetry run python -c "from src.shared.llm_client import LLMClient; client = LLMClient(); print('OK')"
   ```

2. Test generation model specifically:
   ```bash
   poetry run python -c "
   from src.shared.llm_client import LLMClient
   client = LLMClient()
   response = client.generate(
       model_id='openai/gpt-4o-mini',
       messages=[{'role': 'user', 'content': 'Say hi'}]
   )
   print(response)
   "
   ```

3. Run with verbose mode to see error details:
   ```bash
   poetry run python run_eval.py -v
   ```

4. Try with --author filter to test single author:
   ```bash
   poetry run python run_eval.py --author "mark_twain" -v
   ```

---

## API Issues

### Issue: "429 Too Many Requests - Rate limit exceeded"

**Exit Code**: 3 (API error)

**Symptoms**:
```bash
WARNING: Retryable error on attempt 1: 429 Too Many Requests. Retrying in 1s...
WARNING: Retryable error on attempt 2: 429 Too Many Requests. Retrying in 2s...
ERROR: LLM API call failed after 3 attempts
```

**Solutions**:

1. **For OpenRouter**: Check your rate limits and credits:
   - Dashboard: https://openrouter.ai/dashboard
   - Add payment method if needed

2. **Use --author filter** to evaluate subset:
   ```bash
   # Evaluate one author at a time to stay under rate limits
   poetry run python run_eval.py --author "mark_twain"
   # Wait 1-2 minutes, then:
   poetry run python run_eval.py --author "charles_dickens"
   ```

3. Switch to model with higher rate limits:
   ```yaml
   # In eval_config.yml
   generation_model_id: "openai/gpt-3.5-turbo"  # Higher rate limits
   judge_model_id: "openai/gpt-4o-mini"
   ```

4. Disable some metrics to reduce API calls:
   ```yaml
   metrics_judge:
     content_judge: true
     style_judge: false  # Disable to cut judge calls in half
   ```

5. Increase retry delays (custom modification):
   - Edit `src/shared/llm_client.py`
   - Change `retry_delays = [1, 2, 4]` to `retry_delays = [2, 5, 10]`

### Issue: "401 Unauthorized - API authentication failed"

**Exit Code**: 3 (API error)

**Symptoms**:
```bash
ERROR: Authentication error (401): Unauthorized
ERROR: LLM API error: API authentication failed
```

**Solutions**:

1. Verify API key is correct:
   ```bash
   cat .env | grep OPENAI_API_KEY
   # Should show: OPENAI_API_KEY=sk-or-v1-...
   ```

2. For OpenRouter keys:
   - Must start with `sk-or-v1-`
   - Get new key at: https://openrouter.ai/keys

3. For OpenAI keys (direct):
   - Must start with `sk-proj-` or `sk-`
   - Get at: https://platform.openai.com/api-keys
   - Use model ID with `openai/` prefix: `openai/gpt-4o-mini`

4. For Anthropic keys:
   - Must start with `sk-ant-`
   - Use model ID with `anthropic/` prefix: `anthropic/claude-3-5-sonnet-20240620`

5. Check key has not expired:
   ```bash
   # Test with curl
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

---

## Memory and Performance

### Issue: "Out of memory" when computing BERTScore

**Symptoms**:
```bash
RuntimeError: CUDA out of memory
# OR
Killed
```

**Solutions**:

1. **Disable BERTScore** (easiest fix):
   ```yaml
   # In eval_config.yml
   metrics_numeric:
     cosine_similarity: true
     bert_score: false  # Disable
   ```

2. Use GPU if available:
   ```bash
   # Check GPU availability
   poetry run python -c "import torch; print(torch.cuda.is_available())"
   # If True, BERTScore will auto-use GPU (much faster)
   ```

3. Reduce batch size (requires code modification):
   - Edit `src/evaluator/metrics/numeric.py`
   - In `compute_bertscore()`, add `batch_size=8` parameter

4. Evaluate fewer cases at once:
   ```bash
   # Use --author filter
   poetry run python run_eval.py --author "mark_twain"
   ```

### Issue: Evaluation is too slow (>2 hours for 10 cases)

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| **CPU-only BERTScore** | Disable BERTScore or use GPU |
| **Slow LLM model** | Switch to gpt-4o-mini or claude-3-haiku |
| **All metrics enabled** | Disable some metrics (style_judge, bert_score) |
| **Large text files** | Reduce `max_tokens_for_neutralizer` in dataset config |
| **API rate limits** | Use --author filter to evaluate incrementally |

**Recommended fast config**:
```yaml
# eval_config.yml - Fast mode
generation_model_id: "openai/gpt-4o-mini"  # Fast
judge_model_id: "openai/gpt-4o-mini"       # Fast
embedding_model: "all-MiniLM-L6-v2"        # Fast

metrics_numeric:
  cosine_similarity: true   # Fast
  bert_score: false         # Slow - disable

metrics_judge:
  content_judge: true       # Keep one judge
  style_judge: false        # Disable for speed
```

### Issue: Disk space error when saving results

**Exit Code**: 4 (Filesystem error)

**Symptoms**:
```bash
ERROR: Filesystem error: [Errno 28] No space left on device
```

**Solutions**:

1. Check disk space:
   ```bash
   df -h .
   ```

2. Clean old evaluation runs:
   ```bash
   # Results are timestamped: eval_results/YYYYMMDD_HHMMSS/
   ls -lh eval_results/

   # Delete old runs (keep recent ones)
   rm -rf eval_results/20251101_*
   ```

3. Change output path to larger disk:
   ```yaml
   # In eval_config.yml
   output_path: "/path/to/larger/disk/eval_results/"
   ```

---

## Integration Errors

### Issue: "ImportError: No module named 'src.ugly_script'"

**Exit Code**: 5 (Integration error)

**Symptoms**:
```bash
ERROR: Integration error: No module named 'src.ugly_script'
```

**Solutions**:

1. Check Ugly Script exists:
   ```bash
   ls ../src/ugly_script.py
   ```

2. Verify PYTHONPATH includes repository root:
   ```bash
   cd eval_harness
   export PYTHONPATH="$(pwd)/..:$PYTHONPATH"
   poetry run python run_eval.py
   ```

3. Check import path in code:
   ```python
   # In src/evaluator/integration.py
   # Should be: from src.ugly_script import analyze_style, generate_article
   ```

4. If Ugly Script API changed, update adapter:
   - Check `src/evaluator/integration.py`
   - Ensure function signatures match current Ugly Script

### Issue: Style profile format incompatible

**Symptoms**:
```bash
ERROR: generate_article() got unexpected keyword argument 'style_profile'
```

**Solution**:

Check Ugly Script API version:

```bash
cd ..
poetry run python -c "from src.ugly_script import analyze_style; import inspect; print(inspect.signature(analyze_style))"
```

Update `src/evaluator/integration.py` to match current API.

---

## Advanced Debugging

### Enable full debug logging

```bash
poetry run python prepare_dataset.py -v 2>&1 | tee debug.log
poetry run python run_eval.py -v 2>&1 | tee eval_debug.log
```

### Check specific component

```python
# Test LLM client
poetry run python -c "
from src.shared.llm_client import LLMClient
client = LLMClient()
print('LLM client OK')
"

# Test Neutralizer
poetry run python -c "
from src.dataset_builder.neutralizer import Neutralizer
from src.shared.llm_client import LLMClient
n = Neutralizer(LLMClient(), 'openai/gpt-4o-mini', 4000)
print('Neutralizer OK')
"

# Test NumericMetrics
poetry run python -c "
from src.evaluator.metrics.numeric import NumericMetrics
m = NumericMetrics()
print('NumericMetrics OK')
"
```

### Profile memory usage

```bash
poetry add memory_profiler
poetry run python -m memory_profiler run_eval.py
```

---

## Getting More Help

If you're still stuck:

1. **Check logs carefully** - Use `-v` flag for verbose output
2. **Search existing issues** - Check GitHub issues for similar problems
3. **Create minimal reproduction** - Test with 2 authors, 3 cases each
4. **Share error details**:
   - Full error message
   - Config file contents
   - Python/Poetry versions
   - OS and hardware specs

**Documentation Links**:
- [README.md](./README.md) - Main documentation
- [quickstart.md](../specs/003-style-eval-harness/quickstart.md) - Setup guide
- [data-model.md](../specs/003-style-eval-harness/data-model.md) - Config reference
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Development guide
