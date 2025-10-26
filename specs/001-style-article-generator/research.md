# Research & Technology Decisions: Style Article Generator

**Feature**: 001-style-article-generator
**Date**: 2025-10-26
**Purpose**: Resolve all technology choices and unknowns before Phase 1 design

---

## 1. OpenRouter API Integration

### Decision
Use OpenRouter with the `openai` Python library (v1.0+) via base URL override.

### Rationale
- OpenRouter provides OpenAI-compatible API at `https://openrouter.ai/api/v1`
- Same client library (`openai`) eliminates need for custom HTTP client
- Supports all OpenAI SDK features (streaming, async, etc.) though we only need basic completion
- Well-documented migration path

### Implementation Details

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")  # OpenRouter API key
)

# Basic completion call
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",  # Example model
    messages=[{"role": "user", "content": prompt}]
)
```

### Rate Limits & Retry Strategy
- OpenRouter has model-specific rate limits (varies by provider)
- For v0.0.1: No retry logic (constraint: minimal error handling)
- User can manually retry on failure
- **Future enhancement**: Add exponential backoff for 429 errors

### Alternatives Considered
- **Direct HTTP with `requests`**: More code, manual error handling, no streaming support
- **Custom OpenRouter SDK**: Doesn't exist as mature library
- **LangChain**: Too heavy for simple script (90-minute constraint)

**Chosen**: OpenAI SDK with base URL override (minimal code, familiar API)

---

## 2. Loguru Configuration

### Decision
Use Loguru with custom format for colored, structured console output.

### Rationale
- Zero configuration required (works out of box)
- Automatic colorization based on log level
- Supports structured logging with keyword args
- No handlers/formatters boilerplate (vs stdlib `logging`)
- Beautiful default output for CLI tools

### Implementation Details

```python
import sys
from loguru import logger

# Remove default handler
logger.remove()

# Add custom handler for console
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True
)

# Usage examples
logger.info("Fetching content from {count} URLs...", count=3)
logger.success("✓ Cached style profile loaded")
logger.warning("⚠ Failed to fetch {url}: timeout", url="https://example.com")
logger.error("✗ API key not found in .env")
```

### Log Levels for This Project
- **INFO**: Progress updates (fetching, analyzing, generating)
- **SUCCESS**: Positive outcomes (cache hit, article generated)
- **WARNING**: Non-fatal issues (URL fetch failed, continue with others)
- **ERROR**: Fatal issues (missing API key, no content fetched)

### Alternatives Considered
- **stdlib `logging`**: Requires handler/formatter setup, less readable
- **`rich` library**: More features but heavier dependency
- **`colorama` + print**: Manual color codes, no structured logging

**Chosen**: Loguru (perfect fit for CLI tool aesthetics + simplicity)

---

## 3. BeautifulSoup Text Extraction

### Decision
Use `lxml` parser with BeautifulSoup for robust HTML parsing and text extraction.

### Rationale
- `lxml` is faster than `html.parser` and more lenient with malformed HTML
- BeautifulSoup provides high-level API for text extraction
- Handles encoding detection automatically
- Well-tested for web scraping

### Implementation Details

```python
from bs4 import BeautifulSoup
import requests

def extract_text_from_html(html: str) -> str:
    """Extract clean text from HTML, removing scripts/styles/nav."""
    soup = BeautifulSoup(html, 'lxml')

    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        element.decompose()

    # Get text and clean whitespace
    text = soup.get_text(separator=' ', strip=True)

    # Collapse multiple spaces
    text = ' '.join(text.split())

    return text
```

### Elements to Filter
- `<script>` - JavaScript code
- `<style>` - CSS rules
- `<nav>` - Navigation menus
- `<header>`, `<footer>` - Page structure (not article content)
- `<aside>` - Sidebars

### Alternatives Considered
- **`html.parser`**: Slower, stricter with malformed HTML
- **`html5lib`**: Most accurate but very slow
- **`trafilatura`**: Specialized for article extraction but adds complexity
- **`newspaper3k`**: Full-featured but unmaintained

**Chosen**: BeautifulSoup + lxml (good balance of speed/accuracy/simplicity)

---

## 4. Style Profile Hashing

### Decision
Use MD5 hash of sorted, normalized URLs for cache key generation.

### Rationale
- MD5 is fast and sufficient (no security requirement for cache keys)
- Sorting ensures deterministic hashing (order-independent)
- URL normalization prevents cache misses from trivial differences

### Implementation Details

```python
import hashlib
from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    """Normalize URL to canonical form."""
    parsed = urlparse(url)
    # Lowercase scheme and domain, keep path as-is
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower()
    )
    return urlunparse(normalized)

def generate_url_hash(urls: list[str]) -> str:
    """Generate deterministic hash from URL list."""
    # Normalize and sort URLs
    normalized_urls = sorted([normalize_url(url) for url in urls])

    # Create hash
    combined = '\n'.join(normalized_urls)
    return hashlib.md5(combined.encode('utf-8')).hexdigest()
```

### URL Normalization Rules
- Convert scheme to lowercase (HTTP → http)
- Convert domain to lowercase (Example.COM → example.com)
- Preserve path case (case-sensitive)
- Sort URLs alphabetically

### Cache File Naming
- Format: `style_profiles/{hash}.txt`
- Example: `style_profiles/a3f2d1e8c9b4...txt`

### Alternatives Considered
- **SHA256**: More secure but overkill (not hashing passwords)
- **No normalization**: Cache misses from `http` vs `https`
- **URL as filename**: Special characters cause filesystem issues

**Chosen**: MD5 of sorted, normalized URLs (fast, deterministic, filesystem-safe)

---

## 5. Prompt Placeholder System

### Decision
Use Python `str.format()` with dict unpacking for template rendering.

### Rationale
- Built-in Python feature (no dependencies)
- Simple syntax: `{variable_name}`
- Dict unpacking allows flexible context
- Easy to test and debug

### Implementation Details

```python
def render_template(template: str, context: dict) -> str:
    """Render template with placeholders replaced by context values."""
    try:
        return template.format(**context)
    except KeyError as e:
        raise ValueError(f"Missing placeholder in template: {e}")

# Usage
template = "Analyze this {content_length}-character text: {content}"
context = {
    "content": "Lorem ipsum...",
    "content_length": 500
}
rendered = render_template(template, context)
```

### Supported Placeholders

**For `style_analysis.txt`**:
- `{content}` - Extracted text from URLs
- `{content_length}` - Character count

**For `article_generation.txt`**:
- `{topic}` - Article topic
- `{style_profile}` - Generated style analysis

### Error Handling
- Missing placeholder → raise `ValueError` with clear message
- Extra context keys → silently ignored (forward compatibility)

### Alternatives Considered
- **Jinja2**: Too heavy for simple placeholders (adds dependency)
- **`str.replace()`**: Manual tracking of all placeholders
- **f-strings**: Can't load from files (template is runtime data)
- **`string.Template`**: More limited syntax

**Chosen**: `str.format()` (perfect balance of power and simplicity)

---

## 6. Poetry + pytest Integration

### Decision
Use Poetry for dependency management with pytest configured in `pyproject.toml`.

### Rationale
- Poetry manages virtual environments automatically
- Lock file ensures reproducible builds
- Modern alternative to `requirements.txt` + `setup.py`
- pytest is industry standard for Python testing

### Implementation Details

**pyproject.toml** (minimal configuration):

```toml
[tool.poetry]
name = "ugly-script"
version = "0.0.1"
description = "Style-aware article generator"
authors = ["Your Name <email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
openai = "^1.0"
requests = "^2.31"
beautifulsoup4 = "^4.12"
lxml = "^4.9"
python-dotenv = "^1.0"
loguru = "^0.7"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-cov = "^4.1"
pytest-mock = "^3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short --cov=src --cov-report=term-missing"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Test Execution Commands

```bash
# Install dependencies
poetry install

# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_config.py -v

# Run tests matching pattern
poetry run pytest -k "test_fetch"
```

### Test Fixtures Best Practices
- Use `@pytest.fixture` for reusable test data
- Mock external dependencies (`requests`, OpenAI API)
- Keep fixtures in `conftest.py` for sharing across tests

### Alternatives Considered
- **pip + requirements.txt**: No lock file, manual venv management
- **pipenv**: Less active development than Poetry
- **unittest**: Stdlib but more verbose than pytest

**Chosen**: Poetry + pytest (modern, comprehensive, great DX)

---

## 7. TDD Workflow with AICODE Comments

### Decision
Manual grep checks before file modification + AICODE comments after implementation.

### Rationale
- grep is universally available (no setup needed)
- Manual process enforces mindful review
- Pre-commit hooks add complexity (violates 90-minute constraint)
- AICODE comments provide durable knowledge base

### Implementation Details

**Before modifying any file**:

```bash
# Check specific file
grep "AICODE" src/config.py

# Check entire src directory
grep -r "AICODE" src/

# Search for specific types
grep -r "AICODE-TODO" src/
grep -r "AICODE-ASK" src/
```

**After implementing feature**:

```python
# AICODE-NOTE: Using sorted URLs for deterministic cache keys
def generate_url_hash(urls: list[str]) -> str:
    sorted_urls = sorted(urls)
    ...

# AICODE-TODO: Add retry logic for transient network errors
def fetch_url(url: str) -> str:
    ...

# AICODE-ASK: Should we validate URL format before fetching?
```

### Comment Lifecycle
1. **AICODE-ASK**: Question requiring human input
   - After answer: Remove and add AICODE-NOTE with decision
2. **AICODE-TODO**: Pending work
   - After completion: Remove or convert to AICODE-NOTE
3. **AICODE-NOTE**: Permanent documentation
   - Stays in codebase, explains WHY not WHAT

### Alternatives Considered
- **Pre-commit hooks**: Automated but adds setup complexity
- **CI/CD checks**: Overkill for 90-minute project
- **No comments**: Loses context over time
- **Standard Python docstrings**: Don't distinguish AI decisions

**Chosen**: Manual grep + AICODE comments (lightweight, durable)

---

## Summary of Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| **LLM API** | OpenAI SDK + OpenRouter base URL | OpenAI-compatible, minimal code |
| **Logging** | Loguru with custom format | Beautiful CLI output, zero config |
| **HTML Parsing** | BeautifulSoup + lxml | Fast, robust, handles malformed HTML |
| **Cache Keys** | MD5 of sorted normalized URLs | Fast, deterministic, filesystem-safe |
| **Templates** | `str.format()` with dict | Built-in, simple, no dependencies |
| **Dependencies** | Poetry + pytest | Modern Python tooling, lock files |
| **TDD Workflow** | Manual grep + AICODE comments | Lightweight, enforces mindfulness |

All decisions prioritize **simplicity** and **90-minute development constraint** while maintaining code quality and testability.

---

## Next Phase

Proceed to **Phase 1: Design & Contracts** to create:
- data-model.md (entity definitions)
- contracts/prompts.md (prompt structure)
- contracts/configuration.md (config schema)
- quickstart.md (setup guide)
