# Quickstart Guide: Style Article Generator

**Feature**: 001-style-article-generator
**Date**: 2025-10-26
**Time to Complete**: 5-10 minutes

---

## Prerequisites

- **Python 3.11+** installed
- **Poetry** installed ([install instructions](https://python-poetry.org/docs/#installation))
- **OpenRouter API key** ([get one here](https://openrouter.ai/keys))

---

## Step 1: Clone and Setup

```bash
# Navigate to project directory
cd /Users/teterinsa/Projects/TextScript

# Verify you're on the feature branch
git branch
# Should show: * 001-style-article-generator

# Install dependencies using Poetry
poetry install

# Verify installation
poetry run python --version
# Should output: Python 3.11.x or higher
```

**Expected output:**
```
Installing dependencies from lock file
...
Installing the current project: ugly-script (0.0.1)
```

---

## Step 2: Create Configuration File

Create a `.env` file in the project root:

```bash
# Copy the example template
cp .env.example .env

# Edit .env with your API key
nano .env  # or use your preferred editor
```

**Add your OpenRouter API key:**

```bash
# .env
OPENAI_API_KEY=sk-or-v1-YOUR_ACTUAL_KEY_HERE

# Optional: Customize limits (or leave commented for defaults)
# MAX_URLS=10
# MAX_CONTENT_LENGTH_PER_URL=5000
# MAX_TOTAL_CONTENT_LENGTH=8000
# URL_FETCH_TIMEOUT=30
```

**Save and close the file.**

---

## Step 3: Prepare Input Files

### Create links.txt

List URLs you want to analyze (one per line):

```bash
# Create links.txt
cat > links.txt << 'EOF'
https://example.com/article1
https://example.com/article2
https://example.com/article3
EOF
```

**Example** with real URLs:
```
https://paulgraham.com/startupideas.html
https://paulgraham.com/growth.html
https://paulgraham.com/ds.html
```

### Create topic.txt

Specify your article topic (single line):

```bash
# Create topic.txt
echo "The Future of Artificial Intelligence" > topic.txt
```

---

## Step 4: Run the Script

```bash
# Run the main script
poetry run python src/ugly_script.py
```

**Expected output:**
```
08:30:15 | INFO     | Configuration loaded
08:30:15 | INFO     | Reading URLs from links.txt...
08:30:15 | INFO     | Reading topic from topic.txt...
08:30:15 | INFO     | Fetching content from 3 URLs...
08:30:18 | SUCCESS  | ✓ Fetched: https://example.com/article1 (4532 chars)
08:30:21 | SUCCESS  | ✓ Fetched: https://example.com/article2 (3891 chars)
08:30:23 | SUCCESS  | ✓ Fetched: https://example.com/article3 (5124 chars)
08:30:23 | INFO     | Checking for cached style profile...
08:30:23 | INFO     | No cache found. Analyzing style with LLM...
08:30:35 | SUCCESS  | ✓ Style profile generated
08:30:35 | INFO     | Saving style profile to cache...
08:30:35 | INFO     | Generating article on topic: The Future of Artificial Intelligence
08:31:02 | SUCCESS  | ✓ Article generated (782 words)

--- YOUR ARTICLE ---
[Generated article content appears here]
```

The article will be:
1. **Printed to console** (stdout)
2. **Saved to** `output.txt`

---

## Step 5: View Output

### Console Output

The article is displayed in the terminal after generation.

### File Output

```bash
# View the generated article
cat output.txt

# Or open in your editor
nano output.txt
```

### Cached Style Profile

```bash
# List cached profiles
ls -lh style_profiles/

# View a profile
cat style_profiles/a3f2d1e8c9b4abcd.txt
```

---

## Step 6: Run Again with Cache

Run the script again with the **same URLs** but a **different topic**:

```bash
# Change the topic
echo "Building a Successful Startup" > topic.txt

# Run again
poetry run python src/ugly_script.py
```

**Expected output:**
```
08:35:10 | INFO     | Configuration loaded
08:35:10 | INFO     | Reading URLs from links.txt...
08:35:10 | INFO     | Reading topic from topic.txt...
08:35:10 | INFO     | Fetching content from 3 URLs...
08:35:13 | SUCCESS  | ✓ Fetched 3 URLs
08:35:13 | INFO     | Checking for cached style profile...
08:35:13 | SUCCESS  | ✓ Using cached style profile (token savings!)
08:35:13 | INFO     | Generating article on topic: Building a Successful Startup
08:35:35 | SUCCESS  | ✓ Article generated (654 words)

--- YOUR ARTICLE ---
[New article in the same style]
```

**Note**: Style analysis is skipped (saves time and API tokens).

---

## Step 7 (Optional): Customize Prompts

Create custom prompt templates:

```bash
# Create prompts directory
mkdir -p prompts

# Create style analysis prompt
cat > prompts/style_analysis.txt << 'EOF'
You are a literary analyst. Examine this {content_length}-character excerpt and identify:

1. Authorial voice and tone
2. Sentence rhythm and pacing
3. Vocabulary choices
4. Distinctive patterns

Text:
---
{content}
---

Style Profile:
EOF

# Create article generation prompt
cat > prompts/article_generation.txt << 'EOF'
Write a compelling article about: {topic}

Match this writing style exactly:
---
{style_profile}
---

Article (content only, no meta-commentary):
EOF

# Run with custom prompts
poetry run python src/ugly_script.py
```

The script will automatically use your custom prompts instead of defaults.

---

## Running Tests

### Run All Tests

```bash
poetry run pytest
```

**Expected output:**
```
============================= test session starts ==============================
collected 24 items

tests/test_config.py ........                                            [ 33%]
tests/test_url_fetcher.py ......                                         [ 58%]
tests/test_prompt_manager.py ....                                        [ 75%]
tests/test_style_cache.py ....                                           [ 91%]
tests/test_llm_client.py ..                                              [100%]

========================== 24 passed in 3.45s ===============================
```

### Run with Coverage

```bash
poetry run pytest --cov=src --cov-report=term-missing
```

### Run Specific Test

```bash
poetry run pytest tests/test_config.py -v
```

---

## Troubleshooting

### Error: "OPENAI_API_KEY is required"

**Cause**: Missing or empty API key in `.env`

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify API key is set
cat .env | grep OPENAI_API_KEY

# If missing, add it
echo "OPENAI_API_KEY=sk-or-v1-YOUR_KEY" >> .env
```

### Error: "No module named 'openai'"

**Cause**: Dependencies not installed

**Solution**:
```bash
poetry install
```

### Warning: "Failed to fetch URL: timeout"

**Cause**: URL took longer than `URL_FETCH_TIMEOUT` seconds

**Solution**: Increase timeout in `.env`:
```bash
URL_FETCH_TIMEOUT=60
```

### Error: "Missing required placeholder 'content'"

**Cause**: Custom prompt template missing `{content}` placeholder

**Solution**: Add the placeholder to `prompts/style_analysis.txt`:
```text
{content}
```

---

## File Structure After Setup

```
TextScript/
├── .env                     # Your configuration (not in git)
├── .env.example             # Template (in git)
├── links.txt                # Input: URLs to analyze
├── topic.txt                # Input: Article topic
├── output.txt               # Output: Generated article
├── prompts/                 # Optional: Custom prompts
│   ├── style_analysis.txt
│   └── article_generation.txt
├── style_profiles/          # Cached style analyses
│   └── a3f2d1e8c9b4...txt
├── src/                     # Source code
│   ├── ugly_script.py
│   ├── config.py
│   ├── url_fetcher.py
│   ├── prompt_manager.py
│   ├── style_cache.py
│   ├── llm_client.py
│   └── models.py
├── tests/                   # Test files
│   ├── test_config.py
│   ├── test_url_fetcher.py
│   └── ...
├── pyproject.toml           # Poetry configuration
└── README.md                # Project documentation
```

---

## Next Steps

1. **Experiment with different URLs** - Try analyzing different writing styles
2. **Customize prompts** - Tweak the analysis to focus on specific aspects
3. **Adjust limits** - Optimize for speed vs. comprehensiveness
4. **Run tests** - Ensure everything works as expected
5. **Generate multiple articles** - Reuse cached profiles for different topics

---

## Getting Help

- **View logs**: Check console output for detailed error messages
- **Check configuration**: `cat .env` to verify settings
- **Validate inputs**: Ensure `links.txt` and `topic.txt` are not empty
- **Test API key**: Try a minimal request to OpenRouter API
- **Read contracts**: See `specs/001-style-article-generator/contracts/` for detailed specs

---

## Performance Tips

### Speed Up Generation
```bash
# Reduce URLs
MAX_URLS=3

# Reduce content per URL
MAX_CONTENT_LENGTH_PER_URL=2000

# Use cached profiles (same URLs, different topics)
```

### Improve Quality
```bash
# Increase content limits
MAX_URLS=10
MAX_CONTENT_LENGTH_PER_URL=10000
MAX_TOTAL_CONTENT_LENGTH=50000

# Use longer articles for analysis
# (more representative of writing style)
```

---

## Clean Up

To reset and start fresh:

```bash
# Remove generated files
rm output.txt
rm -rf style_profiles/

# Keep configuration and inputs
# (or remove them too if desired)
rm .env links.txt topic.txt
```

---

**You're all set!** Enjoy generating styled articles with your new tool.
