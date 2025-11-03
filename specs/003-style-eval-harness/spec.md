# Feature Specification: StyleGuard - Eval Harness for Article Generation Quality

**Feature Branch**: `003-style-eval-harness`
**Created**: 2025-11-03
**Status**: Draft
**Input**: User description: "StyleGuard: Automated evaluation system for testing article generation quality with numeric metrics and LLM-as-Judge"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Test Dataset from Text Corpus (Priority: P1)

A developer or researcher wants to create a standardized evaluation dataset from a collection of author texts (e.g., Project Gutenberg) to objectively test the article generation system.

**Why this priority**: Without a test dataset, there's no foundation for evaluation. This is the essential first step that enables all other testing capabilities.

**Independent Test**: Can be fully tested by providing a corpus directory with multiple authors and verifying that structured test cases are created in the output directory, each containing source texts, ground truth articles, and neutralized topics.

**Acceptance Scenarios**:

1. **Given** a corpus directory with 3 authors, each having 10+ text files, **When** user runs the dataset builder, **Then** system creates test cases for each author with source texts and ground truth articles
2. **Given** a test case for an author, **When** examining the generated files, **Then** the case includes source_texts.txt (style reference), ground_truth_article.txt (original article), and topic.json (neutralized topic and theses)
3. **Given** an original article with distinctive stylistic features, **When** the neutralizer processes it, **Then** the resulting topic.json contains content-focused theses without stylistic elements
4. **Given** configuration specifying 5 style texts and 5 test cases, **When** builder processes an author with 12 texts, **Then** system randomly splits texts into 5 for style reference and 5 for test cases

---

### User Story 2 - Evaluate Generation Quality with Metrics (Priority: P2)

A developer wants to run the article generation system against the test dataset and receive quantitative measurements of content accuracy and style fidelity.

**Why this priority**: This delivers the core value proposition - objective measurement of generation quality. It depends on having a dataset (P1) but is the main evaluation capability.

**Independent Test**: Can be fully tested by running the evaluator on a prepared test dataset and verifying that it produces numeric metrics (cosine similarity, BERTScore) and qualitative scores (content and style ratings from LLM judges) for each test case.

**Acceptance Scenarios**:

1. **Given** a prepared test dataset with 5 test cases, **When** user runs the evaluation system, **Then** system generates articles for each case and computes all configured metrics
2. **Given** a generated article and ground truth, **When** numeric metrics are computed, **Then** system reports cosine similarity and BERTScore (precision, recall, F1)
3. **Given** a generated article, ground truth, and source texts, **When** LLM judges evaluate, **Then** system returns content score (1-5) and style score (1-5) with reasoning
4. **Given** completed evaluation of multiple test cases, **When** viewing results, **Then** system provides aggregated statistics (mean, median) across all cases
5. **Given** evaluation results, **When** examining output directory, **Then** each test case has generated_article.txt, metrics_numeric.json, metrics_judge_content.json, and metrics_judge_style.json

---

### User Story 3 - Compare Evaluation Runs Over Time (Priority: P3)

A developer wants to track how prompt changes or model updates affect generation quality by comparing evaluation results across multiple runs.

**Why this priority**: This enables iterative improvement and regression detection, but requires both dataset creation and basic evaluation to be working first.

**Independent Test**: Can be fully tested by running evaluation twice with different prompts or models, then verifying that summary reports from both runs can be compared to identify improvements or regressions.

**Acceptance Scenarios**:

1. **Given** two completed evaluation runs with different timestamps, **When** examining summary reports, **Then** each run has distinct results directory with _SUMMARY.csv and _SUMMARY.md
2. **Given** a summary report, **When** reviewing aggregated metrics, **Then** report shows mean values for all metrics across test cases
3. **Given** multiple evaluation runs, **When** comparing summaries, **Then** developer can identify which prompt/model version performs better on content accuracy, style fidelity, or both

---

### User Story 4 - Selective Testing for Debugging (Priority: P3)

A developer working on a specific author's style wants to run evaluation on just that author's test cases to quickly iterate without processing the entire dataset.

**Why this priority**: This is a quality-of-life feature that speeds up development cycles but isn't essential for basic evaluation functionality.

**Independent Test**: Can be fully tested by running evaluation with author filter and verifying that only test cases for that author are processed.

**Acceptance Scenarios**:

1. **Given** a dataset with multiple authors, **When** user runs evaluation specifying a single author name, **Then** system only processes test cases for that author
2. **Given** a filtered evaluation run, **When** reviewing results, **Then** summary statistics reflect only the specified author's test cases

---

### User Story 5 - Baseline Calibration with Perfect Test (Priority: P3)

A developer wants to understand the upper bound of metric quality by running evaluation where "generated" articles are actually the original ground truth texts (perfect reproduction scenario).

**Why this priority**: This provides baseline calibration for interpreting metric scores. Knowing what "perfect" scores look like helps set realistic expectations and detect metric issues.

**Independent Test**: Run `python run_eval.py --perfect-test` on test dataset, verify all metrics show near-perfect scores (cosine similarity ≈1.0, BERTScore ≈1.0, content score = 5, style score = 5).

**Acceptance Scenarios**:

1. **Given** a test dataset with 5 test cases, **When** user runs evaluator with --perfect-test flag, **Then** system skips article generation and uses ground_truth_article.txt as generated output
2. **Given** perfect test mode is enabled, **When** metrics are computed, **Then** cosine similarity scores are ≥0.99 (near perfect semantic match)
3. **Given** perfect test mode is enabled, **When** BERTScore is computed, **Then** F1 scores are ≥0.98 (near perfect token match)
4. **Given** perfect test mode is enabled, **When** LLM judges evaluate, **Then** content scores are 5/5 and style scores reflect that generated text IS the reference style
5. **Given** perfect test results, **When** developer compares with normal evaluation, **Then** gap between perfect and actual scores indicates generation quality headroom

---

### Edge Cases

- What happens when corpus directory contains authors with fewer texts than minimum required (min_texts_per_author)?
- How does system handle text files with non-standard encodings or corrupted data?
- What happens when LLM API calls fail or timeout during dataset generation or evaluation?
- How does system handle very long texts that exceed model context limits?
- What happens when neutralizer returns malformed JSON instead of expected structure?
- How does system handle division by zero or undefined metrics when texts are too short or empty?
- What happens when ground truth article and generated article are identical (perfect reproduction)?

## Requirements *(mandatory)*

### Functional Requirements

**Dataset Builder Component:**

- **FR-001**: System MUST scan corpus directory recursively and identify all authors with at least the minimum required number of text files
- **FR-002**: System MUST randomly split each author's texts into disjoint style reference set and test case set based on configuration
- **FR-003**: System MUST combine multiple style texts into single source_texts.txt file for each test case
- **FR-004**: System MUST preserve one original text as ground_truth_article.txt for each test case
- **FR-005**: System MUST use LLM to extract neutralized topic and content theses from ground truth article, removing stylistic elements
- **FR-006**: System MUST save neutralized content as structured JSON with "topic" and "theses" fields
- **FR-007**: System MUST create organized directory structure: eval_dataset/[author]/case_NNN/ containing all required files
- **FR-008**: System MUST support configuration via YAML file specifying corpus path, output path, text counts, and model selection
- **FR-009**: System MUST display progress indicators during dataset generation
- **FR-010**: System MUST handle text truncation when content exceeds maximum token limits for neutralizer

**Evaluation Component:**

- **FR-011**: System MUST load test cases from eval_dataset directory and extract source texts, topics, and ground truth articles
- **FR-012**: System MUST invoke article generation system (Ugly Script) with source texts and neutralized topic to produce generated article
- **FR-013**: System MUST compute cosine similarity between generated article and ground truth using sentence embeddings
- **FR-014**: System MUST compute BERTScore (precision, recall, F1) between generated article and ground truth
- **FR-015**: System MUST use LLM judge to evaluate content accuracy by comparing generated article to ground truth (1-5 scale)
- **FR-016**: System MUST use LLM judge to evaluate style fidelity by comparing generated article to source texts (1-5 scale)
- **FR-017**: System MUST save generated article and all metric results as separate files in eval_results/[timestamp]/[author]/case_NNN/
- **FR-018**: System MUST support selective evaluation by author name to process subset of test cases
- **FR-019**: System MUST aggregate metrics across all processed test cases and compute mean values
- **FR-020**: System MUST generate summary report in both CSV and markdown formats with aggregated statistics
- **FR-021**: System MUST support configuration via YAML file specifying dataset path, output path, models for generation and judging, and metric toggles
- **FR-022**: System MUST display progress indicators during evaluation
- **FR-023**: System MUST handle metric computation failures gracefully and report errors without stopping entire evaluation
- **FR-024**: System MUST support perfect test mode via CLI flag that uses ground truth article as generated output for baseline metric calibration

**Quality Assurance:**

- **FR-025**: Both components MUST validate configuration files and report specific errors for missing or invalid fields
- **FR-026**: Both components MUST log operations and errors to console with clear context
- **FR-027**: System MUST provide clear CLI help documentation for all commands and options

### Key Entities

- **Test Case**: Represents one evaluation instance for an author, containing source texts for style analysis, a neutralized topic for content generation, and ground truth article for comparison
- **Author**: Represents a writer whose texts are used to create test cases, identified by directory name in corpus
- **Corpus**: Collection of text files organized by author, serving as raw material for dataset generation
- **Evaluation Run**: Time-stamped execution of evaluation process, producing generated articles and metrics for all or selected test cases
- **Metric Result**: Quantitative or qualitative measurement of generation quality, stored as structured data (JSON) alongside generated artifacts
- **Configuration**: YAML-based settings controlling dataset builder or evaluator behavior, including paths, model selection, and feature toggles

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dataset builder processes corpus with 5 authors (each having 10+ texts) and creates complete test datasets in under 30 minutes (excluding LLM API latency)
- **SC-002**: Evaluation system processes 25 test cases (5 authors × 5 cases) and produces complete metrics in under 60 minutes (excluding LLM API latency)
- **SC-003**: Cosine similarity and BERTScore metrics are computed successfully for 100% of test cases where both generated and ground truth articles are non-empty
- **SC-004**: LLM judges return valid scores (1-5 with reasoning) for at least 95% of evaluation attempts (allowing for occasional API failures)
- **SC-005**: Summary reports accurately reflect aggregated statistics from all processed test cases
- **SC-006**: Developer can identify quality regressions by comparing mean content scores and style scores between two evaluation runs
- **SC-007**: System recovers gracefully from at least 90% of individual test case failures, continuing to process remaining cases
- **SC-008**: Generated directory structures and file formats match documented specifications, enabling manual inspection and automated parsing
- **SC-009**: Perfect test mode produces baseline metrics with cosine similarity ≥0.99, BERTScore F1 ≥0.98, and judge scores = 5/5, confirming metrics are calibrated correctly

## Assumptions

1. **LLM API Access**: User has valid API credentials and sufficient quota for calling language models (both neutralizer and judge models)
2. **Corpus Format**: Text corpus follows expected directory structure (corpus/[author]/[text_file.txt]) with UTF-8 encoded files
3. **Article Generator Integration**: Existing "Ugly Script" can be imported as Python module with callable functions for style analysis and article generation
4. **Environment**: Python 3.11+ environment with ability to install required dependencies (openai/anthropic SDK, sentence-transformers, bert-score, etc.)
5. **Storage**: Sufficient disk space for storing corpus, generated datasets (potentially large with many authors), and evaluation results
6. **Text Quality**: Corpus texts are sufficiently long and well-formed for meaningful style analysis and content extraction
7. **Model Availability**: Specified models (e.g., claude-3-5-sonnet-20240620, gpt-4o, meta-llama/llama-3-8b-instruct) are accessible via configured endpoints
8. **Embedding Models**: sentence-transformers models (e.g., all-MiniLM-L6-v2) can be downloaded and loaded locally for computing embeddings
9. **Single-User Context**: System is designed for local development use, not concurrent multi-user access
10. **Text Format**: Corpus texts are plain text files without complex formatting or binary content requiring special preprocessing

## Constraints

- Dataset builder must be stateless and idempotent - running twice with same config produces same results (assuming same random seed)
- Evaluation component must be runnable independently from dataset builder - datasets can be created once and reused for multiple evaluation runs
- System must not modify original corpus files or Ugly Script code
- All LLM API calls must include reasonable timeout and retry logic to handle transient failures
- File naming conventions must be deterministic and avoid special characters to ensure cross-platform compatibility
