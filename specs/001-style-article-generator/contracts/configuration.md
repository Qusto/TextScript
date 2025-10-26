# Configuration Contract

**Feature**: 001-style-article-generator
**Date**: 2025-10-26
**Purpose**: Define `.env` parameters, defaults, and validation rules

---

## Overview

Configuration is loaded from a `.env` file in the working directory. The system provides sensible defaults for all optional parameters.

---

## File Location

**Path**: `.env` (root of working directory)

**Format**: Standard environment file (`KEY=value` pairs)

---

## Parameters

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `OPENAI_API_KEY` | `str` | OpenRouter API key for LLM access | `sk-or-v1-abc123...` |

**No default value**: Script will error if missing.

### Optional Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `MAX_URLS` | `int` | `10` | 1-100 | Maximum number of URLs to process from links.txt |
| `MAX_CONTENT_LENGTH_PER_URL` | `int` | `5000` | 100-50000 | Maximum characters to extract per URL |
| `MAX_TOTAL_CONTENT_LENGTH` | `int` | `8000` | 500-100000 | Maximum total characters for style analysis |
| `URL_FETCH_TIMEOUT` | `int` | `30` | 1-300 | Timeout in seconds for each HTTP request |

---

## Example `.env` File

### Minimal Configuration

```bash
# Required
OPENAI_API_KEY=sk-or-v1-abc123def456...
```

Script will use defaults for all optional parameters.

### Full Configuration

```bash
# Required
OPENAI_API_KEY=sk-or-v1-abc123def456...

# Optional (with custom values)
MAX_URLS=5                          # Process max 5 URLs
MAX_CONTENT_LENGTH_PER_URL=3000     # 3000 chars per URL
MAX_TOTAL_CONTENT_LENGTH=10000      # 10000 chars total
URL_FETCH_TIMEOUT=60                # 60-second timeout
```

---

## Validation Rules

### OPENAI_API_KEY

```python
if not config.api_key:
    raise ValueError(
        "OPENAI_API_KEY is required. "
        "Add it to your .env file: OPENAI_API_KEY=sk-or-v1-..."
    )

if not config.api_key.startswith("sk-"):
    logger.warning("API key doesn't start with 'sk-' - may be invalid format")
```

### MAX_URLS

```python
if config.max_urls <= 0:
    raise ValueError("MAX_URLS must be positive (got {config.max_urls})")

if config.max_urls > 100:
    logger.warning(
        f"MAX_URLS={config.max_urls} is very high. "
        "Consider limiting to reduce execution time."
    )
```

### MAX_CONTENT_LENGTH_PER_URL

```python
if config.max_content_per_url < 100:
    raise ValueError(
        f"MAX_CONTENT_LENGTH_PER_URL too small ({config.max_content_per_url}). "
        "Minimum 100 characters."
    )

if config.max_content_per_url > 50000:
    logger.warning(
        f"MAX_CONTENT_LENGTH_PER_URL={config.max_content_per_url} is very high. "
        "May hit LLM context limits."
    )
```

### MAX_TOTAL_CONTENT_LENGTH

```python
if config.max_total_content < 500:
    raise ValueError(
        f"MAX_TOTAL_CONTENT_LENGTH too small ({config.max_total_content}). "
        "Minimum 500 characters for meaningful style analysis."
    )

if config.max_total_content > config.max_content_per_url * config.max_urls:
    logger.info(
        "MAX_TOTAL_CONTENT_LENGTH > sum of per-URL limits. "
        "Effective limit is per-URL truncation."
    )
```

### URL_FETCH_TIMEOUT

```python
if not (1 <= config.url_fetch_timeout <= 300):
    raise ValueError(
        f"URL_FETCH_TIMEOUT must be 1-300 seconds (got {config.url_fetch_timeout})"
    )
```

---

## Loading Logic

### Order of Precedence

1. **Environment variables** (highest priority)
2. **`.env` file** in current directory
3. **Default values** (lowest priority)

```python
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get values with defaults
api_key = os.getenv("OPENAI_API_KEY", "")
max_urls = int(os.getenv("MAX_URLS", "10"))
max_content_per_url = int(os.getenv("MAX_CONTENT_LENGTH_PER_URL", "5000"))
max_total_content = int(os.getenv("MAX_TOTAL_CONTENT_LENGTH", "8000"))
url_fetch_timeout = int(os.getenv("URL_FETCH_TIMEOUT", "30"))

config = Configuration(
    api_key=api_key,
    max_urls=max_urls,
    max_content_per_url=max_content_per_url,
    max_total_content=max_total_content,
    url_fetch_timeout=url_fetch_timeout
)
```

### Type Conversion

```python
def load_int_param(name: str, default: int) -> int:
    """Load integer parameter with error handling."""
    value_str = os.getenv(name)
    if value_str is None:
        return default

    try:
        return int(value_str)
    except ValueError:
        logger.warning(
            f"Invalid {name}='{value_str}' (not an integer). "
            f"Using default: {default}"
        )
        return default
```

---

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `OPENAI_API_KEY is required` | .env missing or key not set | Add `OPENAI_API_KEY=...` to .env |
| `MAX_URLS must be positive` | Negative or zero value | Set `MAX_URLS=10` or remove (uses default) |
| `URL_FETCH_TIMEOUT must be 1-300 seconds` | Out of range | Set valid timeout (e.g., `URL_FETCH_TIMEOUT=30`) |
| `Invalid MAX_URLS='abc' (not an integer)` | Non-numeric value | Use numeric value or remove (uses default) |

---

## Security Considerations

### API Key Protection

```python
# Never log the full API key
logger.info(f"Using API key: {config.api_key[:7]}...")  # sk-or-v...

# Never commit .env to git
# Add to .gitignore:
.env
```

### .env.example Template

Provide a template file (committed to git) with placeholders:

```bash
# .env.example - Copy to .env and fill in your values

# Required: Get your API key from https://openrouter.ai/keys
OPENAI_API_KEY=sk-or-v1-YOUR_KEY_HERE

# Optional: Uncomment and modify to override defaults
# MAX_URLS=10
# MAX_CONTENT_LENGTH_PER_URL=5000
# MAX_TOTAL_CONTENT_LENGTH=8000
# URL_FETCH_TIMEOUT=30
```

---

## Usage Examples

### Example 1: Token Conservation

Minimize API usage for testing:

```bash
OPENAI_API_KEY=sk-or-v1-abc123...
MAX_URLS=2                          # Only process 2 URLs
MAX_CONTENT_LENGTH_PER_URL=2000     # Limit to 2000 chars per URL
MAX_TOTAL_CONTENT_LENGTH=3000       # Max 3000 chars total
```

### Example 2: Comprehensive Analysis

Analyze more content for better style matching:

```bash
OPENAI_API_KEY=sk-or-v1-abc123...
MAX_URLS=20                         # Process up to 20 URLs
MAX_CONTENT_LENGTH_PER_URL=10000    # 10k chars per URL
MAX_TOTAL_CONTENT_LENGTH=50000      # 50k chars total
URL_FETCH_TIMEOUT=60                # Longer timeout for slow sites
```

### Example 3: Fast Testing

Quick iteration during development:

```bash
OPENAI_API_KEY=sk-or-v1-abc123...
MAX_URLS=1                          # Single URL only
MAX_CONTENT_LENGTH_PER_URL=1000     # Minimal content
MAX_TOTAL_CONTENT_LENGTH=1000
URL_FETCH_TIMEOUT=10                # Fail fast
```

---

## Testing Configuration Loading

```python
def test_load_config_with_defaults():
    """Test that default values are applied."""
    os.environ["OPENAI_API_KEY"] = "sk-test"
    # Don't set optional params

    config = load_configuration()

    assert config.api_key == "sk-test"
    assert config.max_urls == 10  # default
    assert config.max_content_per_url == 5000  # default

def test_load_config_with_overrides():
    """Test that .env overrides defaults."""
    os.environ["OPENAI_API_KEY"] = "sk-test"
    os.environ["MAX_URLS"] = "5"

    config = load_configuration()

    assert config.max_urls == 5  # overridden

def test_missing_api_key_raises_error():
    """Test that missing API key raises ValueError."""
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        load_configuration()
```

---

## Logging Configuration Values

At startup, log the active configuration (except API key):

```python
logger.info("Configuration loaded:")
logger.info(f"  API Key: {config.api_key[:10]}...")
logger.info(f"  MAX_URLS: {config.max_urls}")
logger.info(f"  MAX_CONTENT_LENGTH_PER_URL: {config.max_content_per_url}")
logger.info(f"  MAX_TOTAL_CONTENT_LENGTH: {config.max_total_content}")
logger.info(f"  URL_FETCH_TIMEOUT: {config.url_fetch_timeout}s")
```

---

## Contract Version

**Version**: 1.0.0
**Status**: Stable
**Last Updated**: 2025-10-26
