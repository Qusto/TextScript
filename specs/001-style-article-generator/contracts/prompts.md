# Prompt Template Contract

**Feature**: 001-style-article-generator
**Date**: 2025-10-26
**Purpose**: Define structure and placeholders for LLM prompt templates

---

## Overview

Prompt templates are text files with placeholders that get replaced with actual values at runtime. This allows users to customize LLM behavior without modifying code.

---

## File Locations

| Template | File Path | Purpose |
|----------|-----------|---------|
| Style Analysis | `prompts/style_analysis.txt` | Analyze writing style from source content |
| Article Generation | `prompts/article_generation.txt` | Generate article in analyzed style |

**Note**: If files are missing, the system falls back to built-in default prompts.

---

## Placeholder Format

All placeholders use Python `str.format()` syntax:

```
{variable_name}
```

**Rules**:
- Placeholders are case-sensitive
- Unknown placeholders will cause an error
- Extra context values are ignored (forward compatibility)

---

## style_analysis.txt Contract

### Required Placeholders

| Placeholder | Type | Description | Example Value |
|-------------|------|-------------|---------------|
| `{content}` | `str` | Extracted text content from URLs | "Lorem ipsum dolor..." |
| `{content_length}` | `int` | Character count of content | 8000 |

### Template Example

```text
Analyze the following {content_length}-character text and create a detailed "style profile" of the author.

Describe:
1. Tone (formal, casual, academic, conversational, etc.)
2. Rhythm (short punchy sentences vs long flowing prose)
3. Vocabulary level (simple, technical, academic, poetic)
4. Sentence structure patterns (complexity, variation)
5. Favorite stylistic techniques (metaphors, lists, questions, etc.)

Text to analyze:
---
{content}
---

Provide your analysis as a structured style profile:
```

### Output Format

The LLM response becomes a `StyleProfile.profile_text` string that will be used in article generation.

---

## article_generation.txt Contract

### Required Placeholders

| Placeholder | Type | Description | Example Value |
|-------------|------|-------------|---------------|
| `{topic}` | `str` | Article topic from topic.txt | "The Future of AI" |
| `{style_profile}` | `str` | Generated style analysis | "Tone: conversational..." |

### Template Example

```text
Your task is to write an article on the topic: "{topic}"

You MUST write in the EXACT style described below. Match the tone, rhythm, vocabulary, sentence structure, and techniques precisely.

Style Profile to Imitate:
---
{style_profile}
---

Write ONLY the article content. Do not include any meta-commentary, introductions like "Here is the article:", or explanations. Just the article text itself.

Article:
```

### Output Format

The LLM response becomes a `GeneratedArticle.content` string printed to stdout and optionally saved to `output.txt`.

---

## Default Prompts

If `prompts/` folder or specific template files are missing, the system uses these built-in defaults:

### Default: style_analysis.txt

```python
DEFAULT_STYLE_ANALYSIS = """
Analyze the following {content_length}-character text and create a detailed "style profile" of the author.

Describe:
- Tone (formal, casual, academic, conversational)
- Rhythm (sentence length and variation)
- Vocabulary (simple, technical, academic, poetic)
- Sentence structure patterns
- Stylistic techniques (metaphors, lists, rhetorical questions)

Text:
---
{content}
---

Style Profile:
"""
```

### Default: article_generation.txt

```python
DEFAULT_ARTICLE_GENERATION = """
Write an article about: {topic}

Match this writing style exactly:
---
{style_profile}
---

Write only the article content, no meta-commentary.

Article:
"""
```

---

## Validation Rules

### Template Loading

```python
def load_template(file_path: str) -> PromptTemplate:
    """
    Load template from file or return default.

    Raises:
        ValueError: If template is empty
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            raise ValueError(f"Template file is empty: {file_path}")
        return PromptTemplate(template_text=content, file_path=file_path)
    except FileNotFoundError:
        logger.warning(f"Template not found: {file_path}, using default")
        return get_default_template(file_path)
```

### Placeholder Rendering

```python
def render_template(template: PromptTemplate, context: dict) -> str:
    """
    Render template with context values.

    Raises:
        ValueError: If required placeholder is missing from context
    """
    try:
        return template.template_text.format(**context)
    except KeyError as e:
        missing_key = str(e).strip("'")
        raise ValueError(
            f"Missing required placeholder '{missing_key}' in template "
            f"{template.file_path or 'default'}"
        )
```

---

## Usage Example

### Customizing Style Analysis Prompt

1. Create `prompts/style_analysis.txt`:

```text
You are a literary analyst. Examine this {content_length}-character excerpt:

{content}

Provide a concise style analysis focusing on:
- Authorial voice
- Pacing and flow
- Distinctive patterns
```

2. Run the script:

```bash
poetry run python src/ugly_script.py
```

3. The script will:
   - Load custom template
   - Replace `{content}` and `{content_length}`
   - Send to LLM
   - Cache the result

### Testing Template Rendering

```python
# Test that all placeholders are satisfied
def test_style_analysis_template():
    template = load_template("prompts/style_analysis.txt")
    context = {
        "content": "Sample text...",
        "content_length": 100
    }
    rendered = render_template(template, context)
    assert "{content}" not in rendered
    assert "{content_length}" not in rendered
```

---

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing required placeholder 'content'` | Template doesn't include `{content}` | Add `{content}` to template |
| `Template file is empty` | File exists but has no content | Add template text to file |
| `Unknown placeholder 'author'` | Template uses undefined placeholder | Remove `{author}` or add to context |

---

## Encoding

All template files MUST be UTF-8 encoded to support international characters.

```python
# Always specify encoding when reading/writing
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

---

## Future Extensions

Potential future enhancements (NOT in v0.0.1):

- **Jinja2 templates**: Support control flow (`{% if %}`, `{% for %}`)
- **Template versioning**: Track which template version generated which cache
- **Multi-language templates**: `prompts/style_analysis_ru.txt` for Russian
- **Template validation CLI**: `poetry run python -m ugly_script validate-prompts`

---

## Contract Version

**Version**: 1.0.0
**Status**: Stable
**Last Updated**: 2025-10-26
