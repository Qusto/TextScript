# Prompt Contract: Neutralizer

**Purpose**: Extract neutralized topic and theses from stylized text
**Model**: Configurable (recommended: claude-3-5-sonnet-20240620 or gpt-4o)
**Version**: v1.0
**Used By**: Dataset Builder (`prepare_dataset.py`)

## Prompt Template

### System Message

```text
You are an AI analyst with advanced semantic analysis and summarization skills. Your task is to deconstruct the provided text, separating its stylistic form from its factual content. You must extract "what is said" while completely ignoring "how it is said".

Your goal is to create a stylistically NEUTRAL set of theses.
```

### User Message

```text
Your task is to analyze the following text and return a JSON object with two keys:
1. "topic": A neutral, encyclopedic topic of the text in 1-5 words.
2. "theses": An array of strings containing 5 to 10 key theses, facts, or plot points from the text.

**Critical Requirements for Theses:**
* NEUTRALITY: Theses must be written in dry, impersonal, "bureaucratic" language.
* NO STYLE: Avoid any metaphors, emotionally colored vocabulary, authorial turns of phrase, or rhythmic structure from the original.
* FACTS ONLY: Extract only key facts, events, or arguments.

**EXAMPLE:**
* Original (Stylized): "O, that cursed, damp wind! It howled like a hungry wolf, tearing at my already tormented soul as I trudged through the endless, muddy streets of Paris, seeing nothing..."
* Bad (Style Preserved): ["Wind howled like a wolf", "Soul was tormented", "Streets of Paris were muddy"]
* Good (Neutralized): ["Narrator is located in Paris.", "Weather conditions: strong wind.", "Narrator experiences negative emotions.", "Movement occurs on foot through streets."]

**Response Format:** JSON only.

<OriginalText>
{{ORIGINAL_TEXT}}
</OriginalText>

Analyze the text and return JSON.
```

### Assistant Prefix

```text
```json
```

## Input Parameters

- `{{ORIGINAL_TEXT}}`: Ground truth article text (truncated to max_tokens_for_neutralizer if needed)

## Expected Output

### Success Response

```json
{
  "topic": "Journey through Paris during adverse weather conditions",
  "theses": [
    "Narrator is located in Paris",
    "Weather conditions: strong wind and rain",
    "Narrator experiences negative emotions",
    "Movement occurs on foot through city streets",
    "Time period: evening or night",
    "Narrator is alone during the journey",
    "Physical discomfort from weather is significant"
  ]
}
```

### Output Schema

```typescript
{
  topic: string,        // 1-50 words, neutral phrasing
  theses: string[]      // 5-10 items, each 1-100 words, factual and neutral
}
```

## Validation Rules

The response must satisfy:

1. **Valid JSON**: Parses without errors
2. **Required Fields**: Both `topic` and `theses` present
3. **Topic Length**: 1-50 words, non-empty
4. **Theses Count**: 5-10 items (not fewer, not more)
5. **Theses Content**: Each thesis is non-empty string
6. **Neutrality**: No stylistic language (verified manually during testing)

## Error Handling

### Invalid JSON Response

If the model returns malformed JSON:

```python
try:
    result = json.loads(response)
except JSONDecodeError:
    # Log the raw response
    logger.error(f"Invalid JSON from neutralizer: {response}")
    # Retry with explicit JSON format instruction
    retry_with_format_reminder()
```

### Missing Fields

If required fields are missing:

```python
if 'topic' not in result or 'theses' not in result:
    raise ValueError(f"Missing required fields in neutralizer response: {result.keys()}")
```

### Out of Range Values

If theses count is wrong:

```python
thesis_count = len(result['theses'])
if not (5 <= thesis_count <= 10):
    logger.warning(f"Unexpected thesis count: {thesis_count} (expected 5-10)")
    # Accept anyway if close (4-11), else retry
    if thesis_count < 4 or thesis_count > 11:
        retry_with_count_reminder()
```

## Model-Specific Notes

### Claude (Anthropic)

- Tends to produce well-structured, neutral outputs
- Good at following "no style" instruction
- Occasionally adds extra commentary - parse carefully
- Use `max_tokens: 1000` for output

### GPT-4 (OpenAI)

- Excellent JSON formatting
- May occasionally include subtle stylistic elements
- Sometimes produces fewer theses (4-5) - may need retry
- Use `max_tokens: 800` for output

### Other Models

For other models, test with sample texts and adjust prompt if needed:
- Add more examples if neutrality is poor
- Simplify language if model struggles with instructions
- Increase temperature slightly (0.3-0.5) if outputs are too generic

## Token Management

- **Input**: Truncate original text to `max_tokens_for_neutralizer` (default 4000)
- **Output**: Reserve ~800-1000 tokens for response
- **Total**: ~5000 tokens per API call

**Truncation Strategy**:
```python
def truncate_text(text: str, max_tokens: int) -> str:
    # Approximate: 1 token ≈ 4 characters for English
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    # Truncate at sentence boundary
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    if last_period > max_chars * 0.8:  # Keep if within 80% of max
        return truncated[:last_period + 1]
    return truncated
```

## Quality Assurance

### Manual Review

During initial testing, manually review 10-20 neutralized outputs to verify:
- [ ] No metaphors or poetic language in theses
- [ ] No emotional or subjective descriptions
- [ ] All theses are factual statements
- [ ] Topic accurately captures main subject
- [ ] Thesis count is appropriate (5-10)

### Automated Checks

```python
def validate_neutralization(topic_data: dict) -> bool:
    # Check structure
    if not isinstance(topic_data.get('topic'), str):
        return False
    if not isinstance(topic_data.get('theses'), list):
        return False

    # Check counts
    if not (5 <= len(topic_data['theses']) <= 10):
        return False

    # Check content
    if not topic_data['topic'].strip():
        return False
    for thesis in topic_data['theses']:
        if not isinstance(thesis, str) or not thesis.strip():
            return False

    # Heuristic: check for common stylistic markers
    combined_text = topic_data['topic'] + ' '.join(topic_data['theses'])
    stylistic_markers = ['like a', 'as if', 'seemed to', '!', 'alas', 'oh']
    for marker in stylistic_markers:
        if marker in combined_text.lower():
            logger.warning(f"Possible stylistic language detected: '{marker}'")

    return True
```

## Examples

### Example 1: Narrative Fiction

**Input**:
```text
The old man sat alone in the dusty study, his weathered hands trembling as he turned the yellowed pages of his father's diary. Each word was a dagger to his heart, revealing secrets he had spent a lifetime trying to forget. Outside, the storm raged on, mirror to the tempest within his soul.
```

**Expected Output**:
```json
{
  "topic": "Man reading father's diary in study",
  "theses": [
    "An elderly man is alone in a study",
    "The man is reading a diary belonging to his father",
    "The diary contains previously unknown information",
    "The information causes emotional distress to the reader",
    "The man has avoided confronting this information for many years",
    "Weather conditions: storm occurring outside",
    "The room contains dust, suggesting infrequent use"
  ]
}
```

### Example 2: Descriptive Essay

**Input**:
```text
Venice in autumn is a symphony of gold and crimson, where light dances on ancient waters like whispered secrets between lovers. The city breathes history from every crumbling stone, each canal a vein carrying the lifeblood of a thousand stories yet untold.
```

**Expected Output**:
```json
{
  "topic": "Description of Venice during autumn season",
  "theses": [
    "Location: Venice, Italy",
    "Time period: autumn season",
    "Visual characteristics: gold and crimson colors",
    "Light reflects on water surfaces",
    "City contains historical architecture",
    "Architecture shows signs of age and decay",
    "Canals are present throughout the city"
  ]
}
```

## Version History

- **v1.0** (2025-11-03): Initial prompt design with neutralization focus
