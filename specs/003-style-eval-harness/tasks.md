# Tasks: StyleGuard - Eval Harness for Article Generation Quality

**Input**: Design documents from `/specs/003-style-eval-harness/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are OPTIONAL - This feature follows TDD principle. Tests written first, must FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4) - only for user story phases
- Include exact file paths in descriptions

## Path Conventions

This is a standalone Python CLI project:
- `eval_harness/` - Root directory for evaluation system at repository root
- `eval_harness/src/` - Source code
- `eval_harness/tests/` - Test files
- `eval_harness/configs/` - Example configuration files

**AICODE Comment Style**: All code must include AICODE-NOTE comments explaining:
- Task IDs being implemented
- Key design decisions
- Why specific approaches were chosen
- Integration points with existing systems

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure
**Agent**: `python-backend-developer`

- [X] T001 Create eval_harness/ directory structure at repository root: src/, tests/, configs/
- [X] T002 [P] Create eval_harness/pyproject.toml with Poetry config (Python 3.11+, dependencies from research.md)
- [X] T003 [P] Add dependencies to pyproject.toml: openai, anthropic, pyyaml, sentence-transformers, bert-score, pandas, tqdm, loguru, pytest, pytest-mock
- [X] T004 [P] Run poetry install in eval_harness/ directory
- [X] T005 [P] Create eval_harness/src/__init__.py with package metadata (AICODE-NOTE: T001-T005 - Project structure setup)
- [X] T006 [P] Create eval_harness/configs/dataset_config.yml example with default values from data-model.md
- [X] T007 [P] Create eval_harness/configs/eval_config.yml example with default values from data-model.md
- [X] T008 [P] Create eval_harness/README.md with setup instructions from quickstart.md (AICODE-NOTE: User-facing documentation)
- [X] T009 [P] Create eval_harness/.gitignore for corpus/, eval_dataset/, eval_results/, __pycache__/

**Checkpoint**: Project structure ready - foundational components can now be implemented

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared infrastructure that MUST be complete before ANY user story can be implemented
**⚠️ CRITICAL**: No user story work can begin until this phase is complete
**Agent**: `python-backend-developer`

### Shared Utilities & Configuration Models

- [X] T010 [P] Create eval_harness/src/shared/__init__.py (AICODE-NOTE: Shared utilities package)
- [X] T011 [P] Create eval_harness/src/shared/llm_client.py with unified LLM API client class (AICODE-NOTE: T011 - Reuses .env OPENAI_API_KEY, supports OpenRouter/OpenAI/Anthropic via model ID prefix)
- [X] T012 Implement LLMClient.__init__() in llm_client.py with API key loading from .env and timeout/retry config (AICODE-NOTE: Exponential backoff: 1s, 2s, 4s)
- [X] T013 Implement LLMClient.generate() in llm_client.py with retry logic for rate limits/timeouts (AICODE-NOTE: Retry on 429, 5xx; Don't retry on 401, 400)
- [X] T014 Implement LLMClient._parse_json_response() in llm_client.py with JSON validation (AICODE-NOTE: Handles Claude/GPT JSON formatting differences)
- [X] T015 [P] Create eval_harness/src/shared/file_utils.py with helper functions for reading/writing UTF-8 text files (AICODE-NOTE: T015 - Handles encoding errors gracefully)
- [X] T016 [P] Implement ensure_directory() in file_utils.py with path creation and validation (AICODE-NOTE: Creates parent directories if missing)
- [X] T017 [P] Implement truncate_text() in file_utils.py for token limit truncation at sentence boundaries (AICODE-NOTE: Approximation: 1 token ≈ 4 chars)

### Configuration Models (Pydantic)

- [X] T018 [P] Create eval_harness/src/dataset_builder/__init__.py (AICODE-NOTE: Dataset builder package)
- [X] T019 [P] Create eval_harness/src/dataset_builder/config.py with DatasetConfig Pydantic model from data-model.md (AICODE-NOTE: T019 - Validates m_style_texts + k_test_cases <= min_texts_per_author)
- [X] T020 [P] Add TopicData Pydantic model to dataset_builder/config.py with topic and theses fields (AICODE-NOTE: Validates 5-10 theses, max 100 char topic)
- [X] T021 [P] Create eval_harness/src/evaluator/__init__.py (AICODE-NOTE: Evaluator package)
- [X] T022 [P] Create eval_harness/src/evaluator/config.py with EvalConfig Pydantic model from data-model.md (AICODE-NOTE: T022 - Validates at least one metric enabled)
- [X] T023 [P] Add NumericMetrics, JudgeResult Pydantic models to evaluator/config.py from data-model.md (AICODE-NOTE: Score bounds validation: [0.0-1.0] for numeric, [1-5] for judges)

### Test Fixtures

- [X] T024 [P] Create eval_harness/tests/fixtures/__init__.py (AICODE-NOTE: Shared test fixtures)
- [X] T025 [P] Create eval_harness/tests/fixtures/sample_corpus/ with 2 sample authors (3 texts each) for testing (AICODE-NOTE: Minimal corpus for fast tests)
- [X] T026 [P] Create pytest fixture in eval_harness/tests/conftest.py for mock LLM client (AICODE-NOTE: Prevents real API calls in unit tests)
- [X] T027 [P] Create pytest fixture in eval_harness/tests/conftest.py for temporary directories (AICODE-NOTE: Auto-cleanup with tmp_path)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Test Dataset from Text Corpus (Priority: P1) 🎯 MVP

**Goal**: Core dataset generation - user can run dataset builder on corpus and get structured test cases with neutralized topics
**Independent Test**: Run `python prepare_dataset.py` on sample corpus (3 authors, 10 texts each), verify eval_dataset/ contains author/case_NNN/ subdirectories with source_texts.txt, ground_truth_article.txt, and topic.json for all cases
**Agent**: `python-backend-developer`

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T028 [P] [US1] Contract test for dataset builder CLI in tests/integration/test_dataset_cli.py (AICODE-NOTE: T028 - Tests argparse interface, config loading, exit codes)
- [ ] T029 [P] [US1] Unit test for corpus scanning in tests/unit/test_builder.py (AICODE-NOTE: Tests author discovery, text count filtering)
- [ ] T030 [P] [US1] Unit test for text splitting in tests/unit/test_builder.py (AICODE-NOTE: Tests random split with fixed seed, validates disjoint sets)
- [ ] T031 [P] [US1] Unit test for neutralizer in tests/unit/test_neutralizer.py (AICODE-NOTE: Tests JSON parsing, schema validation, stylistic marker detection)
- [ ] T032 [P] [US1] Integration test for end-to-end dataset generation in tests/integration/test_dataset_pipeline.py (AICODE-NOTE: Uses fixtures/sample_corpus/, validates output structure)

### Implementation for User Story 1

#### Neutralizer Component

- [ ] T033 [P] [US1] Create eval_harness/src/dataset_builder/neutralizer.py with Neutralizer class (AICODE-NOTE: T033 - Implements prompt-neutralizer.md contract)
- [ ] T034 [US1] Implement Neutralizer.__init__() in neutralizer.py with LLM client injection (AICODE-NOTE: Dependency injection for testability)
- [ ] T035 [US1] Implement Neutralizer.neutralize() in neutralizer.py with prompt template from prompt-neutralizer.md (AICODE-NOTE: System + User message structure)
- [ ] T036 [US1] Add JSON response parsing in Neutralizer.neutralize() with TopicData validation (AICODE-NOTE: Falls back to retry with format reminder on malformed JSON)
- [ ] T037 [US1] Add theses count validation in Neutralizer.neutralize() (AICODE-NOTE: Accepts 4-11 theses, strict retries only if <4 or >11)
- [ ] T038 [US1] Implement text truncation in Neutralizer.neutralize() using shared truncate_text() (AICODE-NOTE: Truncates to max_tokens_for_neutralizer before API call)

#### Dataset Builder Component

- [ ] T039 [P] [US1] Create eval_harness/src/dataset_builder/builder.py with DatasetBuilder class (AICODE-NOTE: T039 - Main orchestrator for dataset generation)
- [ ] T040 [US1] Implement DatasetBuilder.__init__() in builder.py with config and LLM client (AICODE-NOTE: Loads DatasetConfig from YAML, initializes Neutralizer)
- [ ] T041 [US1] Implement DatasetBuilder.scan_corpus() in builder.py with recursive directory traversal (AICODE-NOTE: Returns dict[author_name, List[Path]] of text files)
- [ ] T042 [US1] Add author filtering in DatasetBuilder.scan_corpus() based on min_texts_per_author (AICODE-NOTE: Logs warning for skipped authors)
- [ ] T043 [US1] Implement DatasetBuilder._split_texts() in builder.py with random.shuffle() and fixed seed (AICODE-NOTE: Returns (style_set, test_set) tuple, uses config.random_seed if set)
- [ ] T044 [US1] Implement DatasetBuilder._combine_style_texts() in builder.py (AICODE-NOTE: Concatenates M texts with newlines, returns single string)
- [ ] T045 [US1] Implement DatasetBuilder._create_case() in builder.py with file I/O (AICODE-NOTE: Creates case_NNN/ dir, writes 3 files: source_texts.txt, ground_truth_article.txt, topic.json)
- [ ] T046 [US1] Add Neutralizer API call in DatasetBuilder._create_case() with error handling (AICODE-NOTE: Logs error and continues on API failure, doesn't crash entire dataset generation)
- [ ] T047 [US1] Implement DatasetBuilder.generate_dataset() in builder.py with main loop (AICODE-NOTE: Iterates authors with tqdm progress bar, calls _split_texts() and _create_case())
- [ ] T048 [US1] Add logging in DatasetBuilder.generate_dataset() with loguru (AICODE-NOTE: INFO for milestones, DEBUG for details, WARNING for skipped items)

#### CLI Entry Point

- [ ] T049 [US1] Create eval_harness/prepare_dataset.py CLI script (AICODE-NOTE: T049 - Implements cli-dataset-builder.md contract)
- [ ] T050 [US1] Implement argparse in prepare_dataset.py with --config and --verbose flags (AICODE-NOTE: Default config: ./configs/dataset_config.yml)
- [ ] T051 [US1] Add config loading in prepare_dataset.py with YAML parsing and Pydantic validation (AICODE-NOTE: Exit code 1 on config error with specific error message)
- [ ] T052 [US1] Implement main() in prepare_dataset.py with DatasetBuilder instantiation and execution (AICODE-NOTE: Catches exceptions, logs errors, returns appropriate exit codes)
- [ ] T053 [US1] Add progress indicators in prepare_dataset.py using tqdm (AICODE-NOTE: Per-author progress bar showing cases completed)
- [ ] T054 [US1] Add final summary output in prepare_dataset.py (AICODE-NOTE: Authors processed, total test cases, output directory)

**Checkpoint**: MVP complete - dataset generation fully functional

---

## Phase 4: User Story 2 - Evaluate Generation Quality with Metrics (Priority: P2)

**Goal**: Core evaluation - user can run evaluator on dataset and get quality metrics (numeric + LLM judges)
**Independent Test**: Run `python run_eval.py` on generated dataset (10 test cases), verify eval_results/[timestamp]/ contains generated articles and all 4 metric JSON files per case, plus _SUMMARY.csv with aggregated stats
**Agent**: `python-backend-developer`

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T055 [P] [US2] Contract test for evaluator CLI in tests/integration/test_eval_cli.py (AICODE-NOTE: T055 - Tests argparse interface, config loading, --author filter)
- [ ] T056 [P] [US2] Unit test for Ugly Script integration in tests/unit/test_integration.py (AICODE-NOTE: Tests import and function calls)
- [ ] T057 [P] [US2] Unit test for cosine similarity in tests/unit/test_metrics.py (AICODE-NOTE: Tests embedding generation and similarity calculation)
- [ ] T058 [P] [US2] Unit test for BERTScore in tests/unit/test_metrics.py (AICODE-NOTE: Tests precision/recall/F1 calculation)
- [ ] T059 [P] [US2] Unit test for LLM judges in tests/unit/test_metrics.py (AICODE-NOTE: Tests prompt formatting, JSON parsing, score validation)
- [ ] T060 [P] [US2] Integration test for end-to-end evaluation in tests/integration/test_eval_pipeline.py (AICODE-NOTE: Uses fixtures/sample_dataset/, validates all outputs)

### Implementation for User Story 2

#### Ugly Script Integration

- [ ] T061 [P] [US2] Create eval_harness/src/evaluator/integration.py with UglyScriptIntegration class (AICODE-NOTE: T061 - Wrapper for importing and calling Ugly Script functions)
- [ ] T062 [US2] Implement UglyScriptIntegration.analyze_style() in integration.py (AICODE-NOTE: Imports from src.ugly_script, calls analyze_style() with source_texts and model_id)
- [ ] T063 [US2] Implement UglyScriptIntegration.generate_article() in integration.py (AICODE-NOTE: Calls generate_article() with style_profile, topic_data, and model_id)
- [ ] T064 [US2] Add error handling in integration.py for import failures and API errors (AICODE-NOTE: Exit code 5 on integration error with helpful message)

#### Numeric Metrics

- [ ] T065 [P] [US2] Create eval_harness/src/evaluator/metrics/__init__.py (AICODE-NOTE: Metrics package)
- [ ] T066 [P] [US2] Create eval_harness/src/evaluator/metrics/numeric.py with NumericMetricsCalculator class (AICODE-NOTE: T066 - Implements cosine similarity and BERTScore)
- [ ] T067 [US2] Implement NumericMetricsCalculator.__init__() in numeric.py with embedding model loading (AICODE-NOTE: Loads sentence-transformers model, caches for reuse)
- [ ] T068 [US2] Implement NumericMetricsCalculator.cosine_similarity() in numeric.py (AICODE-NOTE: Generates embeddings for both texts, computes cosine via numpy)
- [ ] T069 [US2] Implement NumericMetricsCalculator.bert_score() in numeric.py (AICODE-NOTE: Uses bert-score library, returns precision/recall/F1)
- [ ] T070 [US2] Add error handling in numeric.py for empty texts and computation failures (AICODE-NOTE: Returns None on failure, logs warning, doesn't crash evaluation)

#### LLM Judge Metrics

- [ ] T071 [P] [US2] Create eval_harness/src/evaluator/metrics/judge.py with LLMJudge class (AICODE-NOTE: T071 - Implements content and style judge prompts)
- [ ] T072 [US2] Implement LLMJudge.__init__() in judge.py with LLM client injection (AICODE-NOTE: Dependency injection for testability)
- [ ] T073 [US2] Implement LLMJudge.judge_content() in judge.py with prompt from prompt-content-judge.md (AICODE-NOTE: System + User message, JSON response expected)
- [ ] T074 [US2] Implement LLMJudge.judge_style() in judge.py with prompt from prompt-style-judge.md (AICODE-NOTE: System + User message, JSON response expected)
- [ ] T075 [US2] Add JSON response parsing in judge.py with JudgeResult validation (AICODE-NOTE: Validates score [1-5], reasoning length [50-500 chars])
- [ ] T076 [US2] Add error handling in judge.py for malformed responses and API failures (AICODE-NOTE: Returns None on failure, logs warning)

#### Evaluation Runner

- [ ] T077 [P] [US2] Create eval_harness/src/evaluator/runner.py with EvaluationRunner class (AICODE-NOTE: T077 - Main orchestrator for evaluation)
- [ ] T078 [US2] Implement EvaluationRunner.__init__() in runner.py with config and dependencies (AICODE-NOTE: Initializes UglyScriptIntegration, NumericMetricsCalculator, LLMJudge)
- [ ] T079 [US2] Implement EvaluationRunner._load_test_cases() in runner.py (AICODE-NOTE: Scans eval_dataset/ for case directories, loads files)
- [ ] T080 [US2] Add author filtering in EvaluationRunner._load_test_cases() (AICODE-NOTE: Filters by --author flag if provided)
- [ ] T081 [US2] Implement EvaluationRunner._evaluate_case() in runner.py with all metric computations (AICODE-NOTE: Generates article, computes metrics, saves results)
- [ ] T082 [US2] Add file saving in EvaluationRunner._evaluate_case() (AICODE-NOTE: Saves generated_article.txt and 4 JSON metric files)
- [ ] T083 [US2] Implement EvaluationRunner.run_evaluation() in runner.py with main loop (AICODE-NOTE: Iterates cases with tqdm progress bar per author)
- [ ] T084 [US2] Add error recovery in EvaluationRunner.run_evaluation() (AICODE-NOTE: Logs error, continues to next case on failure)
- [ ] T085 [US2] Implement EvaluationRunner._aggregate_results() in runner.py (AICODE-NOTE: Collects all JSON metrics into pandas DataFrame)
- [ ] T086 [US2] Implement _SUMMARY.csv generation in runner.py (AICODE-NOTE: Computes mean/median/std, saves CSV)
- [ ] T087 [US2] Implement _SUMMARY.md generation in runner.py (AICODE-NOTE: Human-readable report with interpretation)

#### CLI Entry Point

- [ ] T088 [US2] Create eval_harness/run_eval.py CLI script (AICODE-NOTE: T088 - Implements cli-evaluator.md contract)
- [ ] T089 [US2] Implement argparse in run_eval.py with --config, --author, --verbose flags (AICODE-NOTE: Default config: ./configs/eval_config.yml)
- [ ] T090 [US2] Add config loading in run_eval.py with YAML parsing and Pydantic validation (AICODE-NOTE: Exit code 1 on config error)
- [ ] T091 [US2] Add model initialization in run_eval.py with logging (AICODE-NOTE: Logs embedding model, BERTScore model, generation model, judge model)
- [ ] T092 [US2] Implement main() in run_eval.py with EvaluationRunner instantiation and execution (AICODE-NOTE: Creates timestamped output directory)
- [ ] T093 [US2] Add progress indicators in run_eval.py using tqdm (AICODE-NOTE: Per-author progress bar with time estimates)
- [ ] T094 [US2] Add final summary output in run_eval.py (AICODE-NOTE: Cases processed, mean metrics, output directory)

**Checkpoint**: Core evaluation functional - can generate articles and compute quality metrics

---

## Phase 5: User Story 3 - Compare Evaluation Runs Over Time (Priority: P3)

**Goal**: Regression tracking - user can compare results from multiple evaluation runs to detect quality changes
**Independent Test**: Run evaluation twice with different model configs, verify both runs create separate timestamped directories, compare _SUMMARY.csv files to identify metric differences
**Agent**: `python-backend-developer` (documentation only - code already handles this)

### Implementation for User Story 3

- [ ] T095 [US3] Add timestamp-based directory creation in run_eval.py main() (AICODE-NOTE: T095 - Format: YYYYMMDD_HHMMSS, prevents overwriting previous runs)
- [ ] T096 [US3] Document comparison workflow in eval_harness/README.md (AICODE-NOTE: Examples of using diff or pandas to compare CSVs)
- [ ] T097 [US3] Add comparison examples to quickstart.md (AICODE-NOTE: Step-by-step guide for comparing two evaluation runs)

**Checkpoint**: Users can track quality over time by comparing multiple evaluation runs

---

## Phase 6: User Story 4 - Selective Testing for Debugging (Priority: P3)

**Goal**: Fast iteration - developer can run evaluation on single author for quick debugging
**Independent Test**: Run `python run_eval.py --author "mark_twain"`, verify only mark_twain test cases are processed, summary reflects only those cases
**Agent**: `python-backend-developer` (already implemented in T080)

### Implementation for User Story 4

- [ ] T098 [US4] Verify author filtering implementation in EvaluationRunner._load_test_cases() from T080 (AICODE-NOTE: T098 - Already implemented, just needs validation)
- [ ] T099 [US4] Add author filtering examples to eval_harness/README.md (AICODE-NOTE: Command examples with --author flag)
- [ ] T100 [US4] Test author filtering with integration test from T060 (AICODE-NOTE: Validates filtered results match expectations)

**Checkpoint**: Selective evaluation working - fast iteration on specific authors

---

## Phase 7: User Story 5 - Baseline Calibration with Perfect Test (Priority: P3)

**Goal**: Metric calibration - developer can run perfect test mode to establish baseline metrics (≈100% scores) for interpreting real evaluation results
**Independent Test**: Run `python run_eval.py --perfect-test`, verify all metrics show near-perfect scores (cosine≈1.0, BERTScore≈1.0, judges=5/5)
**Agent**: `python-backend-developer`

### Implementation for User Story 5

- [ ] T116 [US5] Add --perfect-test CLI flag to run_eval.py argparse configuration (AICODE-NOTE: T116 - Boolean flag, default False)
- [ ] T117 [US5] Implement perfect_test_mode check in EvaluationRunner._evaluate_case() (AICODE-NOTE: Skip Ugly Script call if perfect_test=True)
- [ ] T118 [US5] Implement ground truth copying in _evaluate_case() when perfect_test=True (AICODE-NOTE: Copy ground_truth_article.txt content as generated_article.txt, no generation)
- [ ] T119 [US5] Add perfect test mode examples to eval_harness/README.md and quickstart.md (AICODE-NOTE: Explains baseline calibration use case, expected scores)

**Checkpoint**: Perfect test mode functional - developers can establish metric baselines

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories
**Agent**: `python-backend-developer`

### Documentation & Examples

- [ ] T120 [P] Add AICODE-NOTE comments to all CLI scripts explaining task implementation (AICODE-NOTE: T120 - Documents which tasks each file implements)
- [ ] T121 [P] Update eval_harness/README.md with troubleshooting section from quickstart.md (AICODE-NOTE: Common errors and solutions)
- [ ] T122 [P] Add example corpus download script to eval_harness/scripts/download_gutenberg.sh (AICODE-NOTE: Automates Project Gutenberg download)
- [ ] T123 [P] Create eval_harness/EXAMPLES.md with real usage examples and output samples (AICODE-NOTE: Shows expected outputs for each user story)

### Code Quality

- [ ] T124 [P] Run ruff linter on all Python files in eval_harness/src/ (AICODE-NOTE: T124 - Enforces Python 3.11+ standards)
- [ ] T125 [P] Add type hints to all public functions in eval_harness/src/ (AICODE-NOTE: Enables mypy static type checking)
- [ ] T126 [P] Add docstrings to all classes and public methods (AICODE-NOTE: Google-style docstrings with examples)
- [ ] T127 Run all tests with pytest -v and ensure 100% pass rate (AICODE-NOTE: Validates all user stories work)

### Performance & Reliability

- [ ] T128 [P] Add connection pooling to LLMClient for better API performance (AICODE-NOTE: T128 - Reuses HTTP connections)
- [ ] T129 [P] Implement caching for embedding model to avoid reloading (AICODE-NOTE: Load once, reuse for all cases)
- [ ] T130 [P] Add GPU detection for BERTScore acceleration (AICODE-NOTE: Auto-detects CUDA, falls back to CPU)
- [ ] T131 Add memory profiling for large datasets (AICODE-NOTE: Logs peak memory usage, warns if approaching limits)

### Final Validation

- [ ] T132 Run quickstart.md validation: follow all steps, verify they work (AICODE-NOTE: T132 - End-to-end manual test)
- [ ] T133 Generate sample evaluation run with 2 authors, 5 cases each (AICODE-NOTE: Creates demo dataset for repository)
- [ ] T134 Add sample output files to eval_harness/examples/ directory (AICODE-NOTE: Shows users what to expect)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - MVP, must complete first
- **User Story 2 (Phase 4)**: Depends on US1 completion (needs dataset) - Core functionality
- **User Story 3 (Phase 5)**: Depends on US2 completion (needs evaluation runs) - Optional enhancement
- **User Story 4 (Phase 6)**: Depends on US2 completion (uses evaluator) - Optional QoL feature
- **User Story 5 (Phase 7)**: Depends on US2 completion (uses evaluator with perfect test mode) - Optional calibration
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - MVP)**: No dependencies on other stories - can start after Foundational
- **User Story 2 (P2)**: REQUIRES US1 complete (needs test dataset to evaluate)
- **User Story 3 (P3)**: REQUIRES US2 complete (needs evaluation runs to compare)
- **User Story 4 (P3)**: REQUIRES US2 complete (uses evaluator with filtering)
- **User Story 5 (P3)**: REQUIRES US2 complete (uses evaluator with perfect test mode)

**Critical Path**: Setup → Foundational → US1 (MVP) → US2 (Core) → US3/US4/US5 (Optional)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Shared utilities before components that use them
- Configuration models before main classes
- Core logic before CLI wrappers
- Integration tests after all components ready

### Parallel Opportunities

**Phase 1 (Setup)**: Tasks T002-T009 can all run in parallel

**Phase 2 (Foundational)**:
- T010-T017 (Shared utilities) can run in parallel
- T018-T020 (Dataset config) can run in parallel with T021-T023 (Evaluator config)
- T024-T027 (Test fixtures) can run in parallel with everything else

**Phase 3 (US1 Tests)**: Tasks T028-T032 can all run in parallel (different test files)

**Phase 3 (US1 Implementation)**:
- T033-T038 (Neutralizer) can run in parallel with T061-T064 (Integration - from US2)
- T039-T048 (Builder) sequential within, but can overlap with Neutralizer

**Phase 4 (US2 Tests)**: Tasks T055-T060 can all run in parallel

**Phase 4 (US2 Implementation)**:
- T061-T064 (Integration), T066-T070 (Numeric), T071-T076 (Judges) can all run in parallel
- T077-T087 (Runner) must wait for metrics to be ready

**Phase 7 (Polish)**: Most tasks (T101-T112) can run in parallel

---

## Parallel Example: User Story 1 (Dataset Generation)

Optimal parallel execution (3 developers):

```bash
# Developer 1: Tests (runs first)
T028, T029, T030, T031, T032

# Developer 2: Neutralizer component
T033, T034, T035, T036, T037, T038

# Developer 3: Dataset Builder component
T039, T040, T041, T042, T043, T044, T045, T046, T047, T048

# All developers: CLI and Integration (sequential after above)
T049, T050, T051, T052, T053, T054
```

**Estimated Time**: ~2-3 days with 3 developers working in parallel

---

## Parallel Example: User Story 2 (Evaluation)

Optimal parallel execution (4 developers):

```bash
# Developer 1: Tests
T055, T056, T057, T058, T059, T060

# Developer 2: Integration + Numeric Metrics
T061, T062, T063, T064, T066, T067, T068, T069, T070

# Developer 3: LLM Judge Metrics
T071, T072, T073, T074, T075, T076

# Developer 4: Evaluation Runner (waits for metrics)
T077, T078, T079, T080, T081, T082, T083, T084, T085, T086, T087

# All developers: CLI (sequential after above)
T088, T089, T090, T091, T092, T093, T094
```

**Estimated Time**: ~3-4 days with 4 developers working in parallel

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Recommended MVP**: User Story 1 (Phase 3) only
- Delivers: Dataset generation from corpus to test cases
- Value: Foundation for all evaluation work
- Timeline: ~2-3 days with TDD approach
- Deliverables:
  - `prepare_dataset.py` CLI tool
  - Complete dataset builder implementation
  - Test suite with 5 integration tests
  - Sample dataset with 2 authors

### Full Feature Scope

**P1 Components** (Must Have):
- User Story 1: Dataset Generation (Phase 3)
- User Story 2: Evaluation with Metrics (Phase 4)

**P2 Components** (Should Have):
- User Story 3: Compare Runs (Phase 5)
- User Story 4: Selective Testing (Phase 6)
- User Story 5: Perfect Test Mode (Phase 7)

**P3 Components** (Nice to Have):
- Phase 8: Polish tasks (documentation, examples, optimization)

### Incremental Delivery Plan

1. **Week 1**: Setup + Foundational + US1 (MVP)
   - Deliverable: Working dataset builder
   - Milestone: Can generate test datasets

2. **Week 2**: US2 (Core evaluation)
   - Deliverable: Working evaluator with all metrics
   - Milestone: Can evaluate generation quality

3. **Week 3**: US3 + US4 + US5 (Optional features)
   - Deliverable: Comparison tools, filtering, and perfect test mode
   - Milestone: Full feature set complete

4. **Week 4**: Phase 8 (Polish)
   - Deliverable: Documentation, examples, optimization
   - Milestone: Production-ready release

### Agent Assignment Summary

**python-backend-developer** agent handles ALL tasks:
- Phase 1: Setup (T001-T009)
- Phase 2: Foundational (T010-T027)
- Phase 3: US1 - Dataset Generation (T028-T054)
- Phase 4: US2 - Evaluation (T055-T094)
- Phase 5: US3 - Comparison (T095-T097)
- Phase 6: US4 - Filtering (T098-T100)
- Phase 7: US5 - Perfect Test (T116-T119)
- Phase 8: Polish (T120-T134)

**Total Tasks**: 134 tasks
- Setup: 9 tasks
- Foundational: 18 tasks
- US1 (MVP): 27 tasks
- US2 (Core): 40 tasks
- US3 (Optional): 3 tasks
- US4 (Optional): 3 tasks
- US5 (Optional): 4 tasks
- Polish: 15 tasks

**Parallel Opportunities**: 45 tasks marked [P] can run concurrently

---

## Success Criteria Validation

After completing all tasks, verify:

- [ ] **SC-001**: Dataset builder processes 5 authors (10+ texts each) in <30 min ✓
- [ ] **SC-002**: Evaluation processes 25 test cases with all metrics in <60 min ✓
- [ ] **SC-003**: Numeric metrics computed for 100% of valid test cases ✓
- [ ] **SC-004**: LLM judges return valid scores for ≥95% of attempts ✓
- [ ] **SC-005**: Summary reports accurately reflect aggregated statistics ✓
- [ ] **SC-006**: Developer can identify regressions by comparing evaluation runs ✓
- [ ] **SC-007**: System recovers from ≥90% of individual test case failures ✓
- [ ] **SC-008**: Directory structures match documented specifications ✓
- [ ] **SC-009**: Perfect test mode produces baseline metrics (cosine≥0.99, BERTScore≥0.98, judges=5/5) ✓

All 9 success criteria from spec.md must pass for feature completion.
