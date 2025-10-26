# Task Breakdown: Style Article Generator

**Feature**: 001-style-article-generator
**Branch**: `001-style-article-generator`
**Date**: 2025-10-26
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Overview

This task breakdown follows **Test-Driven Development (TDD)** with **AICODE comments** workflow. Each task follows the cycle:

```
1. Grep AICODE → 2. Write Tests → 3. Implement → 4. Add AICODE → 5. Verify → 6. Commit → 7. Push
```

**Total Development Time**: 90 minutes (constraint)

---

## Implementation Strategy

### MVP Scope (User Story 1 only)

**Minimum Viable Product** = Phase 3 tasks only:
- Core article generation with style analysis
- Stdout output
- Progress logging with Loguru
- Basic error handling

**Estimated Time**: ~30 minutes (within 90-min constraint)

### Incremental Delivery

After MVP, add features incrementally:
1. **User Story 3** (P1): Single URL support (already in MVP)
2. **User Story 2** (P2): File output
3. **User Story 6** (P2): Caching
4. **User Story 4** (P2): Custom prompts
5. **User Story 5** (P3): Configurable limits

---

## Task Summary

| Phase | User Story | Priority | Task Count | Parallel Tasks |
|-------|------------|----------|------------|----------------|
| Phase 1 | Setup | - | 9 | 0 |
| Phase 2 | Foundational | - | 10 | 4 |
| Phase 3 | US1: Generate Article | P1 | 22 | 6 |
| Phase 4 | US3: Single URL | P1 | 3 | 1 |
| Phase 5 | US2: File Output | P2 | 5 | 2 |
| Phase 6 | US6: Caching | P2 | 11 | 3 |
| Phase 7 | US4: Custom Prompts | P2 | 10 | 3 |
| Phase 8 | US5: Config Limits | P3 | 6 | 2 |
| Phase 9 | Polish | - | 5 | 2 |
| **Total** | **6 Stories** | - | **81** | **23** |

---

## Phase 1: Setup & Environment

**Goal**: Initialize project structure, dependencies, and development tools.

**Duration**: ~10 minutes

### Tasks

- [X] T001 Initialize Poetry project with pyproject.toml in project root
- [X] T002 Add dependencies: openai, requests, beautifulsoup4, lxml, python-dotenv, loguru
- [X] T003 Add dev dependencies: pytest, pytest-cov, pytest-mock
- [X] T004 Create src/ directory structure (ugly_script.py, config.py, url_fetcher.py, prompt_manager.py, style_cache.py, llm_client.py, models.py)
- [X] T005 Create tests/ directory structure (test_config.py, test_url_fetcher.py, test_prompt_manager.py, test_style_cache.py, test_llm_client.py, test_integration.py)
- [X] T006 Create .env.example with template configuration
- [X] T007 Create .gitignore (add .env, style_profiles/, output.txt, __pycache__/, .pytest_cache/)
- [X] T008 Create README.md with quickstart instructions
- [X] T009 Run poetry install to verify setup

**Independent Test**: `poetry install` succeeds, all directories created, .env.example exists

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Build core infrastructure needed by all user stories.

**Duration**: ~15 minutes

**Dependencies**: Phase 1 must complete first.

### Tasks

- [X] T010 Grep for existing AICODE comments in src/
- [X] T011 [P] Write tests for Configuration loading in tests/test_config.py
- [X] T012 [P] Implement Configuration dataclass in src/config.py (load from .env with defaults)
- [X] T013 Add AICODE-NOTE documenting why python-dotenv over os.environ
- [X] T014 Verify tests pass for Configuration: poetry run pytest tests/test_config.py -v
- [X] T015 [P] Write tests for URLSource and ContentCollection in tests/test_url_fetcher.py
- [X] T016 [P] Implement URLSource and ContentCollection dataclasses in src/models.py
- [X] T017 Add AICODE-NOTE explaining truncation strategy for content limits
- [X] T018 Verify tests pass for models: poetry run pytest tests/test_url_fetcher.py::test_models -v
- [X] T019 Commit Phase 2: "feat: add config and data models with TDD"

**Independent Test**: All Phase 2 tests pass (`poetry run pytest tests/test_config.py tests/test_url_fetcher.py -v`)

---

## Phase 3: User Story 1 - Generate Article in Author's Style (P1)

**Goal**: Core MVP - fetch URLs, analyze style, generate article to stdout.

**Duration**: ~25 minutes

**Dependencies**: Phase 2 must complete first.

**Independent Test Criteria**:
1. Given links.txt with 3 URLs, topic.txt with "Test Topic", and .env with API key
2. When `poetry run python src/ugly_script.py` executes
3. Then article is printed to stdout with progress messages

### Tasks

#### URL Fetching (US1)

- [X] T020 Grep AICODE comments in src/
- [X] T021 [P] [US1] Write tests for fetch_url() with requests mocking in tests/test_url_fetcher.py
- [X] T022 [P] [US1] Implement fetch_url() with timeout and error handling in src/url_fetcher.py
- [X] T023 [US1] Add AICODE-NOTE on using requests over urllib for cleaner error handling
- [X] T024 [US1] Verify fetch tests pass: poetry run pytest tests/test_url_fetcher.py::test_fetch -v

#### Text Extraction (US1)

- [X] T025 [P] [US1] Write tests for extract_text_from_html() in tests/test_url_fetcher.py
- [X] T026 [P] [US1] Implement extract_text_from_html() with BeautifulSoup + lxml in src/url_fetcher.py
- [X] T027 [US1] Add AICODE-NOTE on filtering script/style/nav elements
- [X] T028 [US1] Verify extraction tests pass: poetry run pytest tests/test_url_fetcher.py::test_extract -v

#### LLM Integration (US1)

- [X] T029 [P] [US1] Write tests for LLMClient with OpenAI SDK mocking in tests/test_llm_client.py
- [X] T030 [P] [US1] Implement LLMClient with OpenRouter base URL in src/llm_client.py
- [X] T031 [US1] Add AICODE-NOTE on OpenRouter API endpoint configuration
- [X] T032 [US1] Implement StyleProfile and GeneratedArticle dataclasses in src/models.py
- [X] T033 [US1] Verify LLM client tests pass: poetry run pytest tests/test_llm_client.py -v

#### Main Script (US1)

- [X] T034 [US1] Write integration test for end-to-end flow in tests/test_integration.py
- [X] T035 [US1] Implement main() function in src/ugly_script.py orchestrating full workflow
- [X] T036 [US1] Configure Loguru with colored output format at script startup
- [X] T037 [US1] Add progress logging for each major step (fetching, analyzing, generating)
- [X] T038 [US1] Add AICODE-NOTE on Loguru format string for CLI aesthetics
- [X] T039 [US1] Verify integration test passes: poetry run pytest tests/test_integration.py -v
- [X] T040 [US1] Manual test: Create sample links.txt, topic.txt, .env and run script
- [X] T041 [US1] Commit US1: "feat: implement core article generation (US1)"

**Acceptance Verification**:
```bash
# Create test files
echo -e "https://example.com/1\nhttps://example.com/2\nhttps://example.com/3" > links.txt
echo "The Future of AI" > topic.txt
echo "OPENAI_API_KEY=sk-test" > .env

# Run script
poetry run python src/ugly_script.py

# Expected: Progress messages + article printed to stdout
```

---

## Phase 4: User Story 3 - Handle Single URL Input (P1)

**Goal**: Support single URL in links.txt (validate flexibility).

**Duration**: ~5 minutes

**Dependencies**: Phase 3 (US1) must complete first.

**Independent Test Criteria**:
1. Given links.txt with 1 URL
2. When script runs
3. Then style analysis and article generation succeed

### Tasks

- [ ] T042 [P] [US3] Write test for single URL scenario in tests/test_integration.py
- [ ] T043 [US3] Verify ContentCollection handles list with 1 element correctly
- [ ] T044 [US3] Commit US3: "feat: validate single URL support (US3)"

**Acceptance Verification**:
```bash
echo "https://example.com/article" > links.txt
poetry run python src/ugly_script.py
# Expected: Works without errors
```

---

## Phase 5: User Story 2 - Save Generated Content to File (P2)

**Goal**: Write generated article to output.txt.

**Duration**: ~5 minutes

**Dependencies**: Phase 3 (US1) must complete first.

**Independent Test Criteria**:
1. Given successful article generation
2. When script completes
3. Then output.txt exists with article content

### Tasks

- [ ] T045 [P] [US2] Write test for save_to_file() in tests/test_integration.py
- [ ] T046 [P] [US2] Implement save_to_file() in GeneratedArticle class in src/models.py
- [ ] T047 [US2] Add save_to_file() call in main() after stdout print in src/ugly_script.py
- [ ] T048 [US2] Verify file output test passes: poetry run pytest tests/test_integration.py::test_file_output -v
- [ ] T049 [US2] Commit US2: "feat: add file output to output.txt (US2)"

**Acceptance Verification**:
```bash
poetry run python src/ugly_script.py
cat output.txt
# Expected: Article content matches stdout
```

---

## Phase 6: User Story 6 - Reuse Cached Style Profiles (P2)

**Goal**: Cache style profiles by URL hash to save tokens.

**Duration**: ~10 minutes

**Dependencies**: Phase 3 (US1) must complete first.

**Independent Test Criteria**:
1. Run script twice with same links.txt
2. First run: Creates style_profiles/[hash].txt
3. Second run: Loads from cache, skips LLM style analysis

### Tasks

- [X] T050 Grep AICODE comments in src/style_cache.py area
- [X] T051 [P] [US6] Write tests for generate_url_hash() in tests/test_style_cache.py
- [X] T052 [P] [US6] Implement generate_url_hash() with MD5 of sorted URLs in src/style_cache.py
- [X] T053 [US6] Add AICODE-NOTE on MD5 choice (no security needed for cache keys)
- [X] T054 [P] [US6] Write tests for load_from_cache() and save_to_cache() in tests/test_style_cache.py
- [X] T055 [US6] Implement StyleCache class with load/save methods in src/style_cache.py
- [X] T056 [US6] Integrate StyleCache into main() workflow in src/ugly_script.py
- [X] T057 [US6] Add Loguru message "Using cached style profile" when cache hit
- [X] T058 [US6] Verify cache tests pass: poetry run pytest tests/test_style_cache.py -v
- [ ] T059 [US6] Manual test: Run twice with same URLs, verify second run skips analysis
- [X] T060 [US6] Commit US6: "feat: add style profile caching (US6)"

**Acceptance Verification**:
```bash
# First run
poetry run python src/ugly_script.py
ls style_profiles/  # Should show [hash].txt

# Second run with same links.txt
poetry run python src/ugly_script.py
# Expected: Log shows "Using cached style profile"
```

---

## Phase 7: User Story 4 - Customize LLM Prompts (P2)

**Goal**: Load prompts from prompts/*.txt with placeholder replacement.

**Duration**: ~8 minutes

**Dependencies**: Phase 3 (US1) must complete first.

**Independent Test Criteria**:
1. Create prompts/style_analysis.txt with custom text
2. Run script
3. Verify custom prompt is used (check via logging or mock)

### Tasks

- [X] T061 Grep AICODE comments in src/prompt_manager.py area
- [X] T062 [P] [US4] Write tests for PromptTemplate.render() in tests/test_prompt_manager.py
- [X] T063 [P] [US4] Implement PromptTemplate class with str.format() rendering in src/prompt_manager.py
- [X] T064 [US4] Add AICODE-NOTE on choosing str.format over Jinja2 for simplicity
- [X] T065 [US4] Write tests for load_template() with file fallback in tests/test_prompt_manager.py
- [X] T066 [US4] Implement load_template() with default prompts fallback in src/prompt_manager.py
- [X] T066a [P] [US4] Implement default prompt constants (DEFAULT_STYLE_ANALYSIS, DEFAULT_ARTICLE_GENERATION) in src/prompt_manager.py
- [X] T067 [US4] Integrate PromptManager into main() for both prompts in src/ugly_script.py
- [X] T068 [US4] Verify prompt tests pass: poetry run pytest tests/test_prompt_manager.py -v
- [X] T069 [US4] Commit US4: "feat: add custom prompt support (US4)"

**Acceptance Verification**:
```bash
mkdir -p prompts
echo "Analyze this text: {content}" > prompts/style_analysis.txt
poetry run python src/ugly_script.py
# Expected: Custom prompt is used
```

---

## Phase 8: User Story 5 - Configure Content Limits (P3)

**Goal**: Support MAX_URLS, MAX_CONTENT_LENGTH_PER_URL, MAX_TOTAL_CONTENT_LENGTH, URL_FETCH_TIMEOUT in .env.

**Duration**: ~7 minutes

**Dependencies**: Phase 2 (Configuration) and Phase 3 (US1) must complete first.

**Independent Test Criteria**:
1. Set MAX_URLS=2 in .env with 5 URLs in links.txt
2. Run script
3. Verify only 2 URLs are processed

### Tasks

- [ ] T070 [P] [US5] Write tests for limit enforcement in tests/test_url_fetcher.py
- [ ] T071 [P] [US5] Implement limit checks in URLFetcher (max_urls, content truncation) in src/url_fetcher.py
- [ ] T072 [US5] Apply URL_FETCH_TIMEOUT to requests.get() calls in src/url_fetcher.py
- [ ] T073 [US5] Add AICODE-NOTE on default values rationale (from research.md)
- [ ] T074 [US5] Verify limit tests pass: poetry run pytest tests/test_url_fetcher.py::test_limits -v
- [ ] T075 [US5] Commit US5: "feat: add configurable content limits (US5)"

**Acceptance Verification**:
```bash
echo "MAX_URLS=2" >> .env
# Add 5 URLs to links.txt
poetry run python src/ugly_script.py
# Expected: Only first 2 URLs processed
```

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal**: Final touches, documentation, error handling improvements.

**Duration**: ~5 minutes

**Dependencies**: All user story phases complete.

### Tasks

- [ ] T076 [P] Run full test suite with coverage: poetry run pytest --cov=src --cov-report=term-missing
- [ ] T077 [P] Review all AICODE comments: grep -r "AICODE" src/
- [ ] T078 Update README.md with complete usage examples and quickstart
- [ ] T079 Add error messages for common issues (missing files, invalid API key)
- [ ] T080 Commit Polish: "docs: finalize README and error handling"

**Acceptance Verification**:
```bash
poetry run pytest -v
# Expected: All tests pass, coverage >80%
```

---

## Dependency Graph

### Story Completion Order

```
Phase 1: Setup
    ↓
Phase 2: Foundational
    ↓
Phase 3: US1 (P1) ← MVP COMPLETE
    ├→ Phase 4: US3 (P1)
    ├→ Phase 5: US2 (P2)
    ├→ Phase 6: US6 (P2)
    ├→ Phase 7: US4 (P2)
    └→ Phase 8: US5 (P3)
    ↓
Phase 9: Polish
```

### Independent Stories (Can Develop in Parallel after US1)

- **US2** (File Output) - Independent
- **US3** (Single URL) - Independent
- **US4** (Custom Prompts) - Independent
- **US5** (Config Limits) - Independent
- **US6** (Caching) - Independent

**All stories after US1 are parallelizable** - no interdependencies.

---

## Parallel Execution Opportunities

### Phase 2: Foundational (4 parallel tasks)

```bash
# Terminal 1
Task T011-T014: Configuration (tests → implement → AICODE → verify → commit)

# Terminal 2
Task T015-T018: Models (tests → implement → AICODE → verify → commit)
```

### Phase 3: User Story 1 (6 parallel tasks)

```bash
# Terminal 1
Task T021-T024: URL Fetching

# Terminal 2
Task T025-T028: Text Extraction

# Terminal 3
Task T029-T033: LLM Integration
```

### Phase 5-8: Independent Stories (5 parallel streams)

```bash
# Terminal 1: US2 (File Output)
Task T045-T049

# Terminal 2: US3 (Single URL)
Task T042-T044

# Terminal 3: US6 (Caching)
Task T050-T060

# Terminal 4: US4 (Custom Prompts)
Task T061-T069

# Terminal 5: US5 (Config Limits)
Task T070-T075
```

**Maximum Parallelization**: 5 developers can work simultaneously after US1 completes.

---

## TDD + AICODE Workflow (Per Task)

### Step-by-Step Process

```bash
# 1. Grep for existing AICODE comments
grep -r "AICODE" src/module.py

# 2. Write Tests (RED)
# Edit tests/test_module.py
poetry run pytest tests/test_module.py -v
# Verify: Tests FAIL

# 3. Implement Code (GREEN)
# Edit src/module.py
poetry run pytest tests/test_module.py -v
# Iterate until: Tests PASS

# 4. Add AICODE Comments
# Add to src/module.py:
# AICODE-NOTE: [Explain design decision]
# AICODE-TODO: [Mark future work]
# AICODE-ASK: [Flag question for human]

# 5. Verify Tests Pass
poetry run pytest -v

# 6. Commit
git add .
git commit -m "feat: [task description]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 7. Push
git push origin 001-style-article-generator
```

### Example: Task T022 (Implement fetch_url)

```python
# tests/test_url_fetcher.py (Step 2: Write Tests)
def test_fetch_url_success(mocker):
    mock_response = mocker.Mock()
    mock_response.text = "<html>Test content</html>"
    mocker.patch('requests.get', return_value=mock_response)

    result = fetch_url("https://example.com", timeout=30)
    assert result == "<html>Test content</html>"

# src/url_fetcher.py (Step 3: Implement)
import requests
from loguru import logger

# AICODE-NOTE: Using requests over urllib for cleaner API and better error handling
def fetch_url(url: str, timeout: int) -> str:
    """Fetch content from URL with timeout."""
    try:
        logger.info(f"Fetching {url}...")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.Timeout:
        logger.warning(f"Timeout fetching {url}")
        raise
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise

# Step 5: Verify
# poetry run pytest tests/test_url_fetcher.py::test_fetch_url_success -v
# ✓ PASS

# Step 6: Commit
# git commit -m "feat: implement fetch_url with timeout handling (US1)"
```

---

## Time Estimates

| Phase | Tasks | Estimated Time | Cumulative |
|-------|-------|----------------|------------|
| Phase 1: Setup | T001-T009 (9) | 10 min | 10 min |
| Phase 2: Foundational | T010-T019 (10) | 15 min | 25 min |
| Phase 3: US1 (MVP) | T020-T041 (22) | 25 min | 50 min |
| Phase 4: US3 | T042-T044 (3) | 5 min | 55 min |
| Phase 5: US2 | T045-T049 (5) | 5 min | 60 min |
| Phase 6: US6 | T050-T060 (11) | 10 min | 70 min |
| Phase 7: US4 | T061-T069 (9) | 8 min | 78 min |
| Phase 8: US5 | T070-T075 (6) | 7 min | 85 min |
| Phase 9: Polish | T076-T080 (5) | 5 min | **90 min** |

**Total**: 90 minutes (within constraint)

**MVP Only** (Phase 1-3): 50 minutes

---

## Success Criteria

### Per-Story Acceptance

- **US1**: Article printed to stdout with progress messages ✓
- **US2**: Article saved to output.txt ✓
- **US3**: Single URL in links.txt works ✓
- **US4**: Custom prompts from prompts/*.txt used ✓
- **US5**: MAX_URLS limit enforced ✓
- **US6**: Second run with same URLs uses cache ✓

### Global Acceptance

- All 80 tasks completed with checkboxes marked
- All tests pass: `poetry run pytest -v`
- Coverage >80%: `poetry run pytest --cov=src`
- README.md includes quickstart
- All AICODE comments reviewed
- Git history shows TDD commits (test → implement → verify)

---

## Task Format Validation

✅ **All tasks follow required format**:
- Checkbox: `- [ ]`
- Task ID: `T001`, `T002`, etc.
- [P] marker: Present on parallelizable tasks
- [Story] label: Present on user story tasks (US1, US2, etc.)
- Description: Includes file path and clear action

**Example Valid Tasks**:
- `- [ ] T001 Initialize Poetry project with pyproject.toml in project root`
- `- [ ] T022 [P] [US1] Implement fetch_url() with timeout and error handling in src/url_fetcher.py`
- `- [ ] T076 [P] Run full test suite with coverage: poetry run pytest --cov=src`

---

## Getting Started

### Quick Start (MVP)

```bash
# 1. Setup (Phase 1)
poetry install

# 2. Foundational (Phase 2)
# Implement Configuration and Models with TDD

# 3. User Story 1 (Phase 3)
# Implement core article generation

# 4. Test MVP
echo -e "https://example.com/1\nhttps://example.com/2" > links.txt
echo "Test Topic" > topic.txt
echo "OPENAI_API_KEY=sk-test" > .env
poetry run python src/ugly_script.py
```

### Incremental Delivery

After MVP works, add features one story at a time:
1. US3 (Single URL)
2. US2 (File Output)
3. US6 (Caching) ← High value
4. US4 (Custom Prompts)
5. US5 (Config Limits)

---

## Notes

- **90-minute constraint**: Prioritize MVP (US1) first
- **TDD mandatory**: Every task includes test → implement → verify cycle
- **AICODE comments**: Document decisions as you go
- **Parallel execution**: After US1, all stories are independent
- **Loguru logging**: Provides beautiful CLI progress feedback
- **Poetry**: Manages dependencies and virtual env automatically

**Ready to start?** Begin with Task T001!
