# Data Model: Style Article Generator

**Feature**: 001-style-article-generator
**Date**: 2025-10-26
**Purpose**: Define all entities, their attributes, relationships, and state transitions

---

## Entity Diagram

```
┌─────────────────┐
│  Configuration  │
└────────┬────────┘
         │ uses
         ↓
┌─────────────────┐      ┌──────────────────┐
│   URLFetcher    │─────→│   URLSource      │
└────────┬────────┘ fetches  └─────────┬─────┘
         │                              │
         │ extracts content             │ aggregates
         ↓                              ↓
┌─────────────────┐              ┌──────────────────┐
│  ContentCollection│←────────────┤  URLSourceList   │
└────────┬────────┘              └──────────────────┘
         │ generates hash
         ↓
┌─────────────────┐      ┌──────────────────┐
│   StyleCache    │─────→│  StyleProfile    │
└────────┬────────┘ loads/  └─────────┬─────┘
         │         saves              │
         │                            │ uses
         ↓                            ↓
┌─────────────────┐              ┌──────────────────┐
│  PromptManager  │              │  LLMClient       │
└────────┬────────┘              └─────────┬────────┘
         │ renders                          │
         ↓                                  │ generates
┌─────────────────┐                        │
│ PromptTemplate  │←───────────────────────┘
└────────┬────────┘
         │ produces
         ↓
┌─────────────────┐
│ GeneratedArticle│
└─────────────────┘
```

---

## 1. Configuration

**Purpose**: Store runtime configuration loaded from `.env` file with defaults.

### Attributes

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `api_key` | `str` | Yes | None | OpenRouter API key |
| `max_urls` | `int` | No | 10 | Maximum URLs to process from links.txt |
| `max_content_per_url` | `int` | No | 5000 | Maximum characters per URL |
| `max_total_content` | `int` | No | 8000 | Maximum total characters for style analysis |
| `url_fetch_timeout` | `int` | No | 30 | Timeout in seconds for HTTP requests |

### Validation Rules

```python
@dataclass
class Configuration:
    api_key: str
    max_urls: int = 10
    max_content_per_url: int = 5000
    max_total_content: int = 8000
    url_fetch_timeout: int = 30

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        if self.max_urls <= 0:
            raise ValueError("MAX_URLS must be positive")
        if self.max_content_per_url <= 0:
            raise ValueError("MAX_CONTENT_LENGTH_PER_URL must be positive")
        if self.max_total_content <= 0:
            raise ValueError("MAX_TOTAL_CONTENT_LENGTH must be positive")
        if not (1 <= self.url_fetch_timeout <= 300):
            raise ValueError("URL_FETCH_TIMEOUT must be between 1-300 seconds")
```

### State Transitions

1. **Uninitialized** → Load from `.env` → **Validated** (or raise error)

---

## 2. URLSource

**Purpose**: Represent a single URL and its fetched content.

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | `str` | Yes | Original URL from links.txt |
| `content` | `str \| None` | No | Extracted text content (None if fetch failed) |
| `status` | `Literal['success', 'failed']` | Yes | Fetch status |
| `error` | `str \| None` | No | Error message if status == 'failed' |
| `char_count` | `int` | No | Length of content (0 if failed) |

### State Transitions

```
[Created] → fetch() → [Fetched] → extract_text() → [Extracted] → truncate() → [Truncated]
                          ↓ (on error)
                     [Failed]
```

### Example

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class URLSource:
    url: str
    content: str | None = None
    status: Literal['success', 'failed'] = 'failed'
    error: str | None = None

    @property
    def char_count(self) -> int:
        return len(self.content) if self.content else 0

    def truncate(self, max_length: int) -> None:
        """Truncate content to max_length characters."""
        if self.content and len(self.content) > max_length:
            self.content = self.content[:max_length]
```

### Relationships

- **Part of**: ContentCollection (aggregated list)
- **Used by**: URLFetcher (creates instances)

---

## 3. ContentCollection

**Purpose**: Aggregate content from multiple URLSource instances and manage truncation.

### Attributes

| Field | Type | Description |
|-------|------|-------------|
| `sources` | `list[URLSource]` | List of fetched URL sources |
| `combined_content` | `str` | Concatenated content from all successful sources |
| `total_chars` | `int` | Total character count |
| `success_count` | `int` | Number of successfully fetched URLs |
| `failure_count` | `int` | Number of failed URLs |

### Methods

```python
@dataclass
class ContentCollection:
    sources: list[URLSource]

    @property
    def combined_content(self) -> str:
        """Concatenate all successful source content."""
        return "\n\n".join(
            source.content for source in self.sources
            if source.status == 'success' and source.content
        )

    @property
    def total_chars(self) -> int:
        return len(self.combined_content)

    @property
    def success_count(self) -> int:
        return sum(1 for s in self.sources if s.status == 'success')

    @property
    def failure_count(self) -> int:
        return sum(1 for s in self.sources if s.status == 'failed')

    def truncate_to_limit(self, max_total: int) -> None:
        """Truncate combined content to max_total characters."""
        if self.total_chars > max_total:
            # Truncate proportionally or just slice combined_content
            pass  # Implementation detail
```

### State Transitions

```
[Empty] → add sources → [Populated] → truncate_to_limit() → [Truncated]
```

---

## 4. StyleProfile

**Purpose**: Store analyzed writing style characteristics.

### Attributes

| Field | Type | Description |
|-------|------|-------------|
| `profile_text` | `str` | LLM-generated style analysis |
| `source_urls` | `list[str]` | URLs used for analysis |
| `url_hash` | `str` | MD5 hash of sorted URLs (cache key) |
| `cached` | `bool` | True if loaded from cache, False if freshly generated |

### Methods

```python
from dataclasses import dataclass

@dataclass
class StyleProfile:
    profile_text: str
    source_urls: list[str]
    url_hash: str
    cached: bool = False

    @property
    def cache_filename(self) -> str:
        """Return cache file path."""
        return f"style_profiles/{self.url_hash}.txt"

    def save_to_cache(self, cache_dir: str = "style_profiles") -> None:
        """Save profile to cache file."""
        # Implementation: write self.profile_text to cache_filename
        pass

    @classmethod
    def load_from_cache(cls, url_hash: str, urls: list[str]) -> 'StyleProfile | None':
        """Load profile from cache if exists."""
        # Implementation: read from cache file or return None
        pass
```

### State Transitions

```
[Not Cached] → generate via LLM → [Generated] → save_to_cache() → [Saved]
                                                                       ↓
                                                            (next run with same URLs)
                                                                       ↓
[Loaded from Cache] ← load_from_cache()
```

### Relationships

- **Generated by**: LLMClient (first run)
- **Managed by**: StyleCache (save/load operations)

---

## 5. PromptTemplate

**Purpose**: Represent a prompt template with placeholder substitution.

### Attributes

| Field | Type | Description |
|-------|------|-------------|
| `template_text` | `str` | Raw template with `{placeholders}` |
| `file_path` | `str \| None` | Path to template file (None if using default) |
| `is_default` | `bool` | True if using built-in default template |

### Methods

```python
from dataclasses import dataclass

@dataclass
class PromptTemplate:
    template_text: str
    file_path: str | None = None
    is_default: bool = False

    def render(self, context: dict[str, any]) -> str:
        """Render template with context values."""
        try:
            return self.template_text.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing placeholder: {e}")

    @classmethod
    def load_from_file(cls, file_path: str) -> 'PromptTemplate':
        """Load template from file or return default."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return cls(template_text=f.read(), file_path=file_path)
        except FileNotFoundError:
            # Return default template
            return cls.get_default(file_path)

    @classmethod
    def get_default(cls, prompt_type: str) -> 'PromptTemplate':
        """Return built-in default template."""
        defaults = {
            'style_analysis': "Analyze the writing style of this {content_length}-character text...",
            'article_generation': "Write an article about {topic} in the following style: {style_profile}..."
        }
        return cls(template_text=defaults.get(prompt_type, ""), is_default=True)
```

### Supported Placeholders

**style_analysis.txt**:
- `{content}` - Extracted text content
- `{content_length}` - Character count

**article_generation.txt**:
- `{topic}` - Article topic
- `{style_profile}` - Generated style profile text

### Relationships

- **Managed by**: PromptManager
- **Used by**: LLMClient (rendered prompts)

---

## 6. GeneratedArticle

**Purpose**: Represent the final generated article output.

### Attributes

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str` | Article text from LLM |
| `topic` | `str` | Original topic from topic.txt |
| `style_hash` | `str` | Hash of source URLs (links to StyleProfile) |
| `word_count` | `int` | Calculated word count |

### Methods

```python
from dataclasses import dataclass

@dataclass
class GeneratedArticle:
    content: str
    topic: str
    style_hash: str

    @property
    def word_count(self) -> int:
        """Calculate word count."""
        return len(self.content.split())

    def save_to_file(self, file_path: str = "output.txt") -> None:
        """Write article to file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.content)

    def print_to_stdout(self) -> None:
        """Print article to console."""
        print("\n--- YOUR ARTICLE ---")
        print(self.content)
```

### State Transitions

```
[Generated by LLM] → print_to_stdout() → [Displayed]
                   → save_to_file() → [Saved to output.txt]
```

---

## Entity Relationships Summary

```
Configuration
    ↓ (configures)
URLFetcher
    ↓ (creates)
URLSource (many)
    ↓ (aggregated into)
ContentCollection
    ↓ (generates hash)
StyleProfile
    ↓ (cached by)
StyleCache
    ↓ (used with)
PromptTemplate
    ↓ (rendered and sent to)
LLMClient
    ↓ (generates)
GeneratedArticle
```

---

## File-Based Storage

### Input Files

| File | Entity | Format |
|------|--------|--------|
| `.env` | Configuration | `KEY=value` pairs |
| `links.txt` | URLSource (list) | One URL per line |
| `topic.txt` | (topic string) | Single line text |
| `prompts/style_analysis.txt` | PromptTemplate | Text with `{placeholders}` |
| `prompts/article_generation.txt` | PromptTemplate | Text with `{placeholders}` |

### Output Files

| File | Entity | Format |
|------|--------|--------|
| `style_profiles/{hash}.txt` | StyleProfile | Plain text (LLM output) |
| `output.txt` | GeneratedArticle | Plain text (article content) |

---

## Validation Summary

| Entity | Key Validations |
|--------|----------------|
| **Configuration** | api_key not empty, all limits > 0, timeout 1-300 |
| **URLSource** | URL format valid (optional), status in ['success', 'failed'] |
| **ContentCollection** | At least 1 successful source required |
| **StyleProfile** | profile_text not empty, url_hash is valid MD5 |
| **PromptTemplate** | Template renders without KeyError |
| **GeneratedArticle** | content not empty |

All validations should raise clear `ValueError` with actionable messages for debugging.
