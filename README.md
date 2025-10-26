# Text Script - Style Article Generator

Analyze writing style from URLs and generate articles in that style using LLM.

## Quick Start

### 1. Install Dependencies

```bash
poetry install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

### 3. Prepare Input Files

Create `links.txt` with URLs (one per line):
```
https://example.com/article1
https://example.com/article2
```

Create `topic.txt` with your topic:
```
The future of artificial intelligence
```

### 4. Run

```bash
poetry run python -m src.ugly_script
```

## Features

- **Style Analysis**: Fetches content from URLs and analyzes writing style using LLM
- **Article Generation**: Generates articles in the analyzed style on your chosen topic
- **Caching**: Saves style profiles to avoid redundant API calls
- **Customizable Prompts**: Edit prompts in `prompts/` folder
- **Configurable Limits**: Control content length and URL count via `.env`

## Configuration

See `.env.example` for all available options:
- `MAX_URLS`: Maximum number of URLs to process (default: 10)
- `MAX_CONTENT_LENGTH_PER_URL`: Max characters per URL (default: 5000)
- `MAX_TOTAL_CONTENT_LENGTH`: Max total content length (default: 8000)
- `URL_FETCH_TIMEOUT`: Timeout for URL fetching in seconds (default: 30)

## Project Structure

```
text-script/
├── src/
│   ├── ugly_script.py      # Main entry point
│   ├── config.py           # Configuration management
│   ├── url_fetcher.py      # URL fetching and content extraction
│   ├── prompt_manager.py   # Prompt template management
│   ├── style_cache.py      # Style profile caching
│   ├── llm_client.py       # OpenRouter API client
│   └── models.py           # Data models
├── tests/                  # Test suite
├── prompts/                # Customizable prompt templates
├── links.txt               # Input: URLs to analyze
└── topic.txt               # Input: Article topic
```

## License

MIT
