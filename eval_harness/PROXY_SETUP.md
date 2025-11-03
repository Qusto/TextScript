# HTTP Proxy Configuration

This document describes HTTP proxy support for accessing OpenRouter API from regions with restrictions.

## Setup

### 1. Add Proxy to Environment

Add the following to `.env` file in repository root:

```bash
# HTTP Proxy (for regions with API restrictions)
HTTP_PROXY=http://username:password@proxy-server:port
```

**Example:**
```bash
HTTP_PROXY=http://WrSYFwHG:JWXNUurY@172.120.207.144:64636
```

### 2. Verify Proxy Works

Run the test script:

```bash
cd eval_harness
poetry run python test_proxy.py
```

**Expected output:**
```
INFO     | HTTP proxy configured: http://WrSYFwHG:JWXNUurY@172.120.207.144:64636
INFO     | LLMClient initialized (timeout=30s, max_retries=1)
INFO     | Sending test request to OpenRouter...
DEBUG    | Initialized OpenRouter client
SUCCESS  | LLM API call successful (model=gpt-4o-mini)
SUCCESS  | API call successful!
INFO     | Response: Hello, proxy works!
```

## Technical Details

### Implementation

The `LLMClient` class automatically detects `HTTP_PROXY` environment variable and configures all API clients to use it:

1. **httpx Client Creation** (`llm_client.py:77-80`):
   ```python
   self._http_client = httpx.Client(
       proxy=self.http_proxy,
       timeout=timeout
   )
   ```

2. **Proxy Injection** into OpenAI/Anthropic SDKs:
   ```python
   client = OpenAI(
       base_url="https://openrouter.ai/api/v1",
       api_key=self.api_key,
       timeout=self.timeout,
       http_client=self._http_client  # Proxy support
   )
   ```

3. **All providers supported**:
   - ✅ OpenRouter (via OpenAI SDK)
   - ✅ OpenAI direct API
   - ✅ Anthropic API

### Model ID Formats

**Important:** Model ID format determines routing:

| Format | Routes To | Example |
|--------|-----------|---------|
| `gpt-4o-mini` | OpenRouter | ✅ Uses proxy |
| `openai/gpt-4o-mini` | OpenAI Direct | ✅ Uses proxy |
| `anthropic/claude-3-5-sonnet` | Anthropic Direct | ✅ Uses proxy |

**For eval harness:** Use OpenRouter format (no prefix) in `eval_config.yml`:
```yaml
generation_model_id: "gpt-4o-mini"      # ✅ OpenRouter
judge_model_id: "gpt-4o"                # ✅ OpenRouter
```

## Configuration Files

### eval_config.yml

Updated to use OpenRouter format:
```yaml
generation_model_id: "gpt-4o-mini"  # Changed from "meta-llama/..."
judge_model_id: "gpt-4o"            # Changed from "openai/gpt-4o"
```

### perfect_test_config.yml

No changes needed - already uses numeric metrics only (no API calls).

## Troubleshooting

### Issue: 403 Forbidden
**Symptom:**
```
Error code: 403 - unsupported_country_region_territory
```

**Solution:** Ensure `HTTP_PROXY` is set in `.env` and client is initialized after loading environment.

### Issue: 404 Model Not Found
**Symptom:**
```
Error code: 404 - No endpoints found for <model>
```

**Solution:** Check model availability on OpenRouter. Use standard model IDs:
- ✅ `gpt-4o-mini`
- ✅ `gpt-4o`
- ✅ `claude-3-5-sonnet-20241022`

### Issue: 401 Unauthorized (wrong API)
**Symptom:**
```
Error code: 401 - Incorrect API key provided: sk-or-v1-...
```

**Cause:** Model ID with `openai/` prefix routes to OpenAI Direct API, not OpenRouter.

**Solution:** Remove prefix:
- ❌ `openai/gpt-4o-mini` → routes to OpenAI
- ✅ `gpt-4o-mini` → routes to OpenRouter

## Verification

Run full test to verify end-to-end:

```bash
# Test with small dataset (2 authors × 3 cases)
poetry run python run_eval.py --config configs/eval_config.yml -v

# Expected: Generation + evaluation succeed via proxy
```

## Security Notes

- **Never commit `.env` file** - it contains sensitive proxy credentials
- `.env` is already in `.gitignore`
- Proxy credentials are logged (masked) for debugging
- Use HTTPS proxy when possible for encrypted credentials

## Next Steps

With proxy configured, you can now:
1. ✅ Run full evaluation with generation (`run_eval.py`)
2. ✅ Enable LLM judges (content + style scoring)
3. ✅ Test with larger datasets
4. ✅ Use premium models (GPT-4o, Claude 3.5 Sonnet)
