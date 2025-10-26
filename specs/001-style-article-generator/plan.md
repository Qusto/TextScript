# Implementation Plan: Style Article Generator (Ugly Script)

**Branch**: `001-style-article-generator` | **Date**: 2025-10-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-style-article-generator/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a Python CLI script that fetches content from URLs, analyzes writing style using OpenRouter LLM API, and generates articles matching that style. Key capabilities: external prompt templates, configurable content limits via `.env`, style profile caching for token savings, and progress logging with Loguru. Development follows strict TDD with AICODE comments, Poetry dependency management, and 90-minute time constraint.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- `openai` - OpenRouter API client (OpenAI-compatible)
- `requests` - HTTP client for URL fetching
- `beautifulsoup4` - HTML parsing and text extraction
- `python-dotenv` - Environment variable loading
- `loguru` - Structured console logging with colors
- `poetry` - Dependency management and packaging

**Storage**: File-based (no database)
- Input files: `links.txt`, `topic.txt`, `.env`, `prompts/*.txt`
- Output files: `output.txt`, `style_profiles/[hash].txt`

**Testing**: `pytest` with TDD approach
- Test framework: `pytest`
- Mocking: `pytest-mock` or `unittest.mock`
- Coverage: `pytest-cov`

**Target Platform**: CLI tool (Linux/macOS/Windows with Python 3.11+)

**Project Type**: Single standalone script project

**Performance Goals**:
- Total execution time <5 minutes for 3 URLs (first run)
- <2.5 minutes with cached style profile (50% reduction)
- URL fetch timeout: 30s per URL (configurable)

**Constraints**:
- Development time: 90 minutes maximum
- No async/await (synchronous execution only)
- No web framework (FastAPI/Flask)
- No Docker containerization
- Basic error handling only (try-except)
- Must use OpenRouter.ai API (not direct OpenAI)

**Scale/Scope**:
- Process up to 10 URLs (default, configurable via MAX_URLS)
- Content limit: 8000 characters total for style analysis (configurable)
- Single-file script architecture (can be split into modules if needed)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: No project-specific constitution exists yet. Applying general best practices:

### Development Workflow Principles (from user requirements)

✅ **TDD Mandatory**: Tests → Implement → Verify → Commit
✅ **AICODE Comments System**: Document decisions with `# AICODE-NOTE:`, `# AICODE-TODO:`, `# AICODE-ASK:`
✅ **Poetry for Dependencies**: Modern Python dependency management
✅ **Loguru for Logging**: Beautiful, structured console output

### Workflow Compliance

- **Gate 1: Test-First Development**
  - Status: ✅ PASS
  - Evidence: FR-029 requires TDD workflow; user explicitly requires "tests first, then code"

- **Gate 2: Code Documentation**
  - Status: ✅ PASS
  - Evidence: AICODE comment system integrated into workflow

- **Gate 3: Simplicity**
  - Status: ✅ PASS
  - Evidence: Single script, file-based I/O, synchronous execution, 90-minute time box

- **Gate 4: Observability**
  - Status: ✅ PASS
  - Evidence: Loguru for structured logging with progress updates (FR-025)

**Result**: All gates PASSED. Proceed to Phase 0.

---

### Post-Phase 1 Re-evaluation

**Date**: 2025-10-26 (after design artifacts completed)

- **Gate 1: Test-First Development**
  - Status: ✅ PASS
  - Evidence: data-model.md includes validation examples, contracts/ define testable interfaces

- **Gate 2: Code Documentation**
  - Status: ✅ PASS
  - Evidence: AICODE comments integrated into TDD workflow (plan.md Development Workflow section)

- **Gate 3: Simplicity**
  - Status: ✅ PASS
  - Evidence: 7 modular Python files in src/, file-based storage, no databases/APIs, clear separation of concerns

- **Gate 4: Observability**
  - Status: ✅ PASS
  - Evidence: Loguru configuration documented in research.md with progress messages for all stages

**Additional Checks**:

- **Data Model Complexity**: ✅ PASS - 6 simple entities with clear relationships, no ORMs
- **Dependency Count**: ✅ PASS - 6 primary dependencies (all justified in research.md)
- **File I/O Security**: ✅ PASS - UTF-8 encoding specified, no eval/exec, API key protection documented

**Result**: All gates PASSED after Phase 1 design. Ready for Phase 2 (task generation via /speckit.tasks).

## Project Structure

### Documentation (this feature)

```text
specs/001-style-article-generator/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── prompts.md       # Prompt template contract
├── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
└── checklists/
    └── requirements.md  # Spec validation checklist
```

### Source Code (repository root)

```text
# Single script project structure
src/
├── ugly_script.py       # Main script entry point
├── config.py            # Configuration loading (.env + defaults)
├── url_fetcher.py       # URL fetching and content extraction
├── prompt_manager.py    # Prompt template loading and rendering
├── style_cache.py       # Style profile caching (hash + I/O)
├── llm_client.py        # OpenRouter API integration
└── models.py            # Data classes (URLSource, StyleProfile, etc.)

tests/
├── test_config.py           # Test .env loading and defaults
├── test_url_fetcher.py      # Test URL fetching with mocking
├── test_prompt_manager.py   # Test prompt loading and placeholders
├── test_style_cache.py      # Test caching logic and hash generation
├── test_llm_client.py       # Test LLM API calls with mocking
└── test_integration.py      # End-to-end test with sample data

# Project files
pyproject.toml           # Poetry configuration
README.md                # Project documentation
.env.example             # Example environment file

# Runtime files (not in git)
.env                     # User configuration
links.txt                # Input: URLs
topic.txt                # Input: Topic
output.txt               # Output: Generated article
prompts/                 # Prompt templates (optional)
├── style_analysis.txt
└── article_generation.txt
style_profiles/          # Cached style profiles
└── [hash].txt
```

**Structure Decision**: Using a **single project** structure with modular Python files in `src/` directory. This keeps the codebase simple while allowing separation of concerns (fetching, caching, prompts, LLM). Tests mirror the `src/` structure. Poetry manages dependencies. The 90-minute constraint favors this flat, discoverable layout over complex packaging.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All design decisions align with simplicity and TDD principles.

---

## Phase 0: Research & Technology Decisions

**Status**: Pending (will be filled in research.md)

**Research Tasks**:

1. **OpenRouter API Integration**
   - Research: How to use OpenRouter with `openai` Python library
   - Question: What's the base URL and authentication method?
   - Question: Are there rate limits or retry strategies needed?

2. **Loguru Configuration**
   - Research: Best practices for Loguru console logging
   - Question: How to configure colored output with log levels?
   - Question: How to format progress messages effectively?

3. **BeautifulSoup Text Extraction**
   - Research: Best practices for extracting clean text from HTML
   - Question: Which parser (lxml, html.parser) is most reliable?
   - Question: How to filter out scripts, styles, navigation?

4. **Style Profile Hashing**
   - Research: Hash algorithm for URL list (MD5 vs SHA256)
   - Question: Should URLs be sorted before hashing?
   - Question: How to handle URL normalization (http vs https)?

5. **Prompt Placeholder System**
   - Research: Simple string template approach for Python
   - Question: Use `str.format()`, `str.replace()`, or `jinja2`?
   - Decision: Prefer simplest approach (str.format with dict)

6. **Poetry + pytest Integration**
   - Research: Poetry test scripts and coverage reporting
   - Question: How to configure pytest in pyproject.toml?
   - Question: Best practices for test fixtures and mocking?

7. **TDD Workflow with AICODE Comments**
   - Research: Grep integration into test workflow
   - Question: Should AICODE checks be automated via pre-commit?
   - Decision: Manual grep before each file modification

**Output**: research.md with decisions and rationale for each item above

---

## Phase 1: Design Artifacts

**Status**: Pending

### Data Model (data-model.md)

**Entities to define**:

1. **Configuration**
   - Fields: api_key, max_urls, max_content_per_url, max_total_content, url_timeout
   - Validation: api_key required, numeric limits positive
   - Source: `.env` file with defaults

2. **URLSource**
   - Fields: url (str), content (str), status (success/failed), error (optional str)
   - Relationships: Part of ContentCollection
   - State: fetched → extracted → truncated

3. **StyleProfile**
   - Fields: profile_text (str), source_urls (list[str]), hash (str), cached (bool)
   - State: generated → saved OR loaded from cache

4. **PromptTemplate**
   - Fields: template_text (str), placeholders (dict), file_path (str)
   - Operations: load_from_file(), render(context)

5. **GeneratedArticle**
   - Fields: title (optional str), content (str), topic (str), style_hash (str)
   - Output: stdout + optional output.txt

### Contracts (contracts/)

#### Prompt Template Contract

**File**: `contracts/prompts.md`

Defines the structure and placeholders for prompt templates:

```markdown
# Prompt Template Contract

## Placeholder Format

All placeholders use Python str.format syntax: `{variable_name}`

## Required Placeholders

### style_analysis.txt
- `{content}` - Extracted text content from URLs
- `{content_length}` - Character count of content

### article_generation.txt
- `{topic}` - Article topic from topic.txt
- `{style_profile}` - Generated style analysis text

## Default Prompts

Fallback prompts are defined in prompt_manager.py when files are missing.
```

#### Configuration Contract

**File**: `contracts/configuration.md`

Defines `.env` parameters and defaults:

```markdown
# Configuration Contract

## Required Parameters
- `OPENAI_API_KEY` - OpenRouter API key (no default)

## Optional Parameters (with defaults)
- `MAX_URLS=10` - Maximum URLs to process
- `MAX_CONTENT_LENGTH_PER_URL=5000` - Max chars per URL
- `MAX_TOTAL_CONTENT_LENGTH=8000` - Max total chars for analysis
- `URL_FETCH_TIMEOUT=30` - Fetch timeout in seconds

## Validation Rules
- api_key must not be empty
- All numeric values must be positive integers
- Timeout must be 1-300 seconds
```

### Quickstart (quickstart.md)

**File**: `specs/001-style-article-generator/quickstart.md`

Step-by-step guide for:
1. Poetry setup (`poetry install`)
2. Creating `.env` file
3. Creating `links.txt` and `topic.txt`
4. Running the script (`poetry run python src/ugly_script.py`)
5. Viewing output and cached profiles
6. Customizing prompts (optional)
7. Running tests (`poetry run pytest`)

---

## Phase 2: Task Breakdown

**Status**: Deferred to `/speckit.tasks` command

**Note**: This section is intentionally not filled by `/speckit.plan`. The `/speckit.tasks` command will:
1. Read this plan
2. Generate dependency-ordered task list in `tasks.md`
3. Create actionable checklist items
4. Map tasks to TDD workflow (write test → implement → verify → commit)

---

## Development Workflow Integration

### TDD Cycle (per task)

```bash
# 1. Grep for existing AICODE comments
grep -r "AICODE" src/

# 2. Write Tests
# - Create test file: tests/test_[module].py
# - Write failing tests for new functionality
# - Run: poetry run pytest tests/test_[module].py -v
# - Verify: Tests FAIL (red)

# 3. Implement Code
# - Write minimal implementation in src/[module].py
# - Run tests again: poetry run pytest tests/test_[module].py -v
# - Iterate until tests PASS (green)

# 4. Add AICODE comments
# - Document decisions with # AICODE-NOTE: [why this approach]
# - Mark pending work with # AICODE-TODO: [future task]
# - Flag questions with # AICODE-ASK: [question for human]

# 5. Verify Tests Pass
# - Run full test suite: poetry run pytest -v
# - Check coverage: poetry run pytest --cov=src tests/

# 6. Commit
# - git add .
# - git commit -m "feat: [task description]"

# 7. Push
# - git push origin 001-style-article-generator
```

### AICODE Comment Examples

```python
# AICODE-NOTE: Using requests instead of urllib for cleaner API and better error handling
import requests

# AICODE-NOTE: MD5 hash is sufficient for cache keys (no security requirement here)
def generate_url_hash(urls: list[str]) -> str:
    sorted_urls = sorted(urls)  # AICODE-NOTE: Sort for deterministic hashing
    return hashlib.md5("".join(sorted_urls).encode()).hexdigest()

# AICODE-TODO: Add retry logic for transient network errors
def fetch_url(url: str, timeout: int) -> str:
    response = requests.get(url, timeout=timeout)
    return response.text

# AICODE-ASK: Should we validate URL format before fetching?
def process_urls(urls: list[str]) -> list[URLSource]:
    ...
```

### Loguru Logging Pattern

```python
from loguru import logger

# Configure at script start
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")

# Usage in code
logger.info("Fetching content from {count} URLs...", count=len(urls))
logger.success("Cached style profile found - skipping analysis")
logger.warning("Failed to fetch {url}: {error}", url=url, error=str(e))
logger.error("API key not found in .env file")
```

---

## Next Steps

After `/speckit.plan` completes:

1. **Review research.md** - Validate technology decisions
2. **Review data-model.md** - Confirm entity definitions
3. **Review contracts/** - Verify prompt and config contracts
4. **Review quickstart.md** - Test setup instructions
5. **Run `/speckit.tasks`** - Generate actionable task list
6. **Begin TDD cycle** - Implement tasks following workflow above

**Estimated Timeline**:
- Phase 0 (Research): 10 minutes
- Phase 1 (Design): 15 minutes
- Phase 2 (Implementation via tasks.md): 65 minutes
- **Total**: 90 minutes (within constraint)
