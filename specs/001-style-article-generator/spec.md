# Feature Specification: Style Article Generator (Ugly Script)

**Feature Branch**: `001-style-article-generator`
**Created**: 2025-10-26
**Status**: Draft
**Input**: User description: "ТЗ №2: 'Ugly Script' v0.0.1 - Python script that fetches content from URLs, analyzes writing style using LLM (OpenRouter.ai), and generates articles in that style. Inputs: links.txt (URLs), topic.txt (article topic), .env (API key). Output: Generated article to stdout. Stack: Python 3, openai, requests, beautifulsoup4, python-dotenv. Time constraint: 90 minutes development. Test-driven development approach."

## Input Structure

### Required Files

- `links.txt` - List of URLs to analyze (one per line)
- `topic.txt` - Topic for the new article (single line)
- `.env` - Configuration file with the following parameters:
  - `OPENAI_API_KEY` - OpenRouter API key (required)
  - `MAX_URLS` - Maximum number of URLs to process (default: 10)
  - `MAX_CONTENT_LENGTH_PER_URL` - Maximum characters to extract per URL (default: 5000)
  - `MAX_TOTAL_CONTENT_LENGTH` - Maximum total characters for style analysis (default: 8000)
  - `URL_FETCH_TIMEOUT` - Timeout in seconds for fetching each URL (default: 30)

### Prompts Folder

- `prompts/style_analysis.txt` - Prompt template for analyzing writing style
- `prompts/article_generation.txt` - Prompt template for generating the article

The prompt files can contain placeholders:
- `{content}` - Will be replaced with extracted content
- `{content_length}` - Will be replaced with content character count
- `{style_profile}` - Will be replaced with the generated style profile
- `{topic}` - Will be replaced with the article topic

### Style Profiles Cache

- `style_profiles/` - Directory for caching analyzed style profiles
- Profile files are named using a hash of the source URLs (e.g., `style_profiles/abc123def456.txt`)
- If a profile exists for the current set of URLs, it is reused instead of re-analyzing (saves API tokens)
- Each profile file contains the LLM-generated style analysis text

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Article in Author's Style (Priority: P1)

A content creator wants to generate a new article on a specific topic that matches the writing style of existing articles from reference URLs.

**Why this priority**: This is the core value proposition - automating the style analysis and article generation workflow that was previously done manually in the "Консьерж-MVP".

**Independent Test**: Can be fully tested by providing sample URLs and a topic, running the script, and verifying that a coherent article is generated and output to console. Delivers immediate value as a standalone tool.

**Acceptance Scenarios**:

1. **Given** a file `links.txt` with 3 valid URLs, a file `topic.txt` with "The Future of AI", and valid API credentials in `.env`, **When** the script is executed, **Then** the script fetches content from all URLs, analyzes the style, generates an article, and prints it to stdout
2. **Given** the same valid inputs, **When** the script completes execution, **Then** the generated article demonstrates stylistic consistency with the source content (matching tone, vocabulary, sentence structure)
3. **Given** valid inputs, **When** the script runs, **Then** progress messages are displayed for each major step (fetching content, analyzing style, generating article)

---

### User Story 2 - Save Generated Content to File (Priority: P2)

A user wants to save the generated article to an output file for later editing or publishing.

**Why this priority**: Adds convenience for users who want to preserve and edit the output, but the script still delivers value without this feature (stdout works).

**Independent Test**: Can be tested by running the script and verifying that an `output.txt` file is created with the generated article content.

**Acceptance Scenarios**:

1. **Given** valid inputs, **When** the script completes successfully, **Then** the generated article is written to `output.txt` in the current directory
2. **Given** an existing `output.txt` file, **When** the script runs again, **Then** the file is overwritten with the new content

---

### User Story 3 - Handle Single URL Input (Priority: P1)

A user provides a single URL in `links.txt` to analyze and mimic the style from just one source.

**Why this priority**: Essential for scenarios where the user wants to mimic a specific author or publication from a single reference article.

**Independent Test**: Can be tested with `links.txt` containing only one URL and verifying successful style analysis and article generation.

**Acceptance Scenarios**:

1. **Given** `links.txt` with one valid URL, **When** the script runs, **Then** style analysis is performed on that single source and article is generated successfully
2. **Given** a single URL input, **When** style analysis occurs, **Then** the style profile captures characteristics from that one source

---

### User Story 4 - Customize LLM Prompts (Priority: P2)

A user wants to customize the prompts used for style analysis and article generation by editing text files in the `prompts/` folder.

**Why this priority**: Provides flexibility for advanced users to fine-tune the LLM behavior without modifying code, but core functionality works with default prompts.

**Independent Test**: Can be tested by modifying `prompts/style_analysis.txt` with custom instructions, running the script, and verifying the output reflects the customized prompt.

**Acceptance Scenarios**:

1. **Given** custom prompts in `prompts/` folder, **When** the script runs, **Then** the custom prompts are used for LLM API calls
2. **Given** placeholders like `{content}` and `{topic}` in prompt files, **When** the script processes them, **Then** placeholders are replaced with actual values
3. **Given** no `prompts/` folder exists, **When** the script runs, **Then** default built-in prompts are used as fallback

---

### User Story 5 - Configure Content Limits (Priority: P3)

A user wants to configure limits for URL processing (max URLs, max content length, timeout) via `.env` to control execution time and API costs.

**Why this priority**: Useful for managing large-scale operations and costs, but reasonable defaults work for most use cases.

**Independent Test**: Can be tested by setting `MAX_URLS=2` in `.env` with 5 URLs in `links.txt`, and verifying only 2 URLs are processed.

**Acceptance Scenarios**:

1. **Given** `MAX_URLS=5` in `.env` and 10 URLs in `links.txt`, **When** the script runs, **Then** only the first 5 URLs are processed
2. **Given** `MAX_CONTENT_LENGTH_PER_URL=1000` in `.env`, **When** a URL has 5000 characters, **Then** only the first 1000 characters are extracted
3. **Given** `MAX_TOTAL_CONTENT_LENGTH=3000` in `.env`, **When** combined content exceeds 3000 characters, **Then** content is truncated to fit the limit
4. **Given** `URL_FETCH_TIMEOUT=10` in `.env`, **When** a URL takes longer than 10 seconds to respond, **Then** that URL is skipped with a warning message

---

### User Story 6 - Reuse Cached Style Profiles (Priority: P2)

A user runs the script multiple times with the same set of URLs to generate different articles, and wants to reuse the previously analyzed style profile to save API tokens and time.

**Why this priority**: Significantly reduces cost and execution time for repeated use with the same sources, but the script works without caching.

**Independent Test**: Can be tested by running the script twice with identical URLs - the first run creates the cache, the second run should skip style analysis and reuse the cached profile.

**Acceptance Scenarios**:

1. **Given** the same URLs in `links.txt` as a previous run, **When** the script executes, **Then** the cached style profile is loaded and style analysis is skipped
2. **Given** a cached style profile exists, **When** the script runs, **Then** a progress message indicates "Using cached style profile"
3. **Given** URLs in `links.txt` have changed, **When** the script runs, **Then** a new style analysis is performed and a new profile is cached
4. **Given** a cached profile exists in `style_profiles/`, **When** generating an article, **Then** the cached profile is used instead of calling the LLM for style analysis (saves tokens)

---

### Edge Cases

- What happens when `links.txt` contains invalid URLs or URLs that return 404/500 errors?
- What happens when `links.txt` is empty or missing?
- What happens when `topic.txt` is empty or missing?
- What happens when `.env` file is missing or `OPENAI_API_KEY` is invalid?
- What happens when the fetched web content contains very little text (e.g., mostly images/videos)?
- What happens when the LLM API call fails or times out?
- What happens when a URL contains content that cannot be parsed by BeautifulSoup?
- What happens when the total content from all URLs exceeds the context window limit?
- What happens when network connectivity is lost during URL fetching?
- What happens when `prompts/` folder or prompt files are missing?
- What happens when prompt files contain invalid placeholders?
- What happens when configured limits in `.env` are invalid (negative numbers, non-numeric values)?
- What happens when a saved style profile file is corrupted or empty?
- What happens when multiple URLs are provided but all of them fail to fetch?

## Requirements *(mandatory)*

### Functional Requirements

#### Core Input/Output

- **FR-001**: Script MUST read a list of URLs from a file named `links.txt`, with one URL per line
- **FR-002**: Script MUST read the article topic from a file named `topic.txt` (single line)
- **FR-003**: Script MUST load configuration from a `.env` file with the following parameters:
  - `OPENAI_API_KEY` (required) - OpenRouter API key
  - `MAX_URLS` (optional, default: 10) - Maximum number of URLs to process
  - `MAX_CONTENT_LENGTH_PER_URL` (optional, default: 5000) - Maximum characters per URL
  - `MAX_TOTAL_CONTENT_LENGTH` (optional, default: 8000) - Maximum total characters for style analysis
  - `URL_FETCH_TIMEOUT` (optional, default: 30) - Timeout in seconds for URL fetching
- **FR-004**: Script MUST print the generated article to stdout (console output)
- **FR-005**: Script SHOULD optionally write the generated article to an `output.txt` file
- **FR-006**: Script MUST execute as a standalone command-line tool without requiring command-line arguments (all input from files)

#### URL Fetching and Content Extraction

- **FR-007**: Script MUST fetch web content from each URL in `links.txt` using HTTP requests
- **FR-008**: Script MUST respect the `MAX_URLS` limit - process only the first N URLs from `links.txt`
- **FR-009**: Script MUST apply `URL_FETCH_TIMEOUT` to each URL fetch request
- **FR-010**: Script MUST extract clean text content from fetched HTML using text parsing
- **FR-011**: Script MUST truncate content from each URL to `MAX_CONTENT_LENGTH_PER_URL` characters
- **FR-012**: Script MUST truncate combined content to `MAX_TOTAL_CONTENT_LENGTH` before sending to LLM

#### Prompt Management

- **FR-013**: Script MUST load prompt templates from the `prompts/` folder:
  - `prompts/style_analysis.txt` - for style analysis
  - `prompts/article_generation.txt` - for article generation
- **FR-014**: Script MUST replace placeholders in prompt templates with actual values:
  - `{content}` → extracted content
  - `{content_length}` → character count
  - `{style_profile}` → generated style profile
  - `{topic}` → article topic from `topic.txt`
- **FR-015**: Script MUST fall back to built-in default prompts if `prompts/` folder or prompt files are missing

#### Style Profile Caching

- **FR-016**: Script MUST generate a unique hash/fingerprint based on the list of URLs in `links.txt`
- **FR-017**: Script MUST check if a style profile exists in `style_profiles/` directory matching the URL hash
- **FR-018**: Script MUST reuse existing style profile if found (skip LLM style analysis call)
- **FR-019**: Script MUST save the generated style profile to `style_profiles/[hash].txt` after LLM analysis
- **FR-020**: Script MUST create `style_profiles/` directory if it doesn't exist

#### LLM Integration

- **FR-021**: Script MUST send extracted content to OpenRouter LLM API with the loaded style analysis prompt (only if no cached profile exists)
- **FR-022**: Script MUST generate a "style profile" describing the author's tone, rhythm, vocabulary, sentence structure, and writing techniques
- **FR-023**: Script MUST send the article generation prompt to the LLM with the style profile and topic
- **FR-024**: Script MUST use the OpenRouter.ai API endpoint (compatible with OpenAI client library)

#### Progress and Error Handling

- **FR-025**: Script MUST display progress messages indicating current operation (fetching content, analyzing style, generating article, using cached profile)
- **FR-026**: Script MUST handle basic errors with try-except blocks (file not found, network errors, API errors)
- **FR-027**: Script MUST display informative error messages when required files are missing
- **FR-028**: Script MUST continue execution if some URLs fail to fetch (skip failed URLs with warning)

#### Development Workflow

- **FR-029**: Script MUST support test-driven development workflow (tests written before implementation)

### Key Entities

- **URL Source**: Represents a web page referenced in `links.txt` - contains a URL string and the fetched text content (truncated to configured limits)
- **Style Profile**: Represents the analyzed writing characteristics - contains descriptions of tone, rhythm, vocabulary patterns, sentence structure patterns, and stylistic techniques (can be cached and reused)
- **Article Topic**: Represents the subject for the new article - contains a text description from `topic.txt`
- **Generated Article**: Represents the final output - contains text content written in the analyzed style on the specified topic
- **Prompt Template**: Represents a customizable LLM prompt - contains template text with placeholders that are replaced with actual values at runtime
- **Cached Style Profile**: Represents a saved style analysis - stored as a text file in `style_profiles/` directory, named by URL hash for retrieval
- **Configuration**: Represents runtime parameters loaded from `.env` - contains API key, content limits, timeout settings with default fallbacks

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a styled article by providing URLs and a topic, with total execution time under 5 minutes for 3 URLs (first run with style analysis)
- **SC-002**: Cached style profile reduces execution time by at least 50% on subsequent runs with same URLs
- **SC-003**: The script successfully fetches and processes content from at least 90% of valid URLs provided
- **SC-004**: Generated articles demonstrate clear stylistic similarity to source content as validated by manual review (subjective assessment acceptable for v0.0.1)
- **SC-005**: Script provides clear progress feedback with at least 4 status updates during execution (including cache status)
- **SC-006**: Script can be developed, tested, and made functional within 90 minutes following test-driven development approach
- **SC-007**: Generated articles are coherent, on-topic, and at least 300 words in length
- **SC-008**: Script handles common error scenarios (missing files, network errors, invalid limits) without crashing
- **SC-009**: Users can customize prompts by editing text files without modifying code
- **SC-010**: Content limits prevent excessive API token usage - total content stays within configured limits

### Assumptions

- OpenRouter.ai API is compatible with OpenAI client library syntax
- Users have Python 3.x installed on their system
- Users have internet connectivity to fetch URLs and access the LLM API
- The `.env` file format follows standard conventions (`KEY=value`)
- Source URLs contain sufficient text content (at least 500 words total) for meaningful style analysis
- The LLM context window is large enough to accommodate the configured `MAX_TOTAL_CONTENT_LENGTH` plus prompts
- Users understand this is a "quick and dirty" script optimized for speed over robustness
- Output quality depends on the quality and consistency of source URLs provided
- The script will be run from a directory where required files (`links.txt`, `topic.txt`, `.env`) are present or accessible
- BeautifulSoup can extract meaningful text from standard HTML pages without custom parsing rules
- The OpenRouter API endpoint follows OpenAI-compatible format
- Default values for optional `.env` parameters are reasonable for most use cases
- Prompt templates use simple placeholder syntax (`{variable_name}`) for easy editing
- Style profile caching uses MD5 hash algorithm (per research.md decision) based on sorted URL list
- The `style_profiles/` directory can be created and written to by the script
- Users have write permissions for creating `style_profiles/` and `output.txt` in the working directory
- Cached style profiles remain valid across script executions (no expiration logic needed for v0.0.1)
- Multiple runs with different topics but same URLs benefit from style profile reuse
- Prompt files are encoded in UTF-8 for proper text handling

### Constraints

- Development time limited to 90 minutes total
- No web framework (FastAPI/Flask) or REST API implementation
- No database or persistent storage beyond file I/O
- No asynchronous processing - synchronous execution only
- No argument parsing - all input from files
- No graphical user interface
- Minimal error handling - basic try-except only
- No Docker containerization
- Must use OpenRouter.ai (not direct OpenAI API)
- Test-driven development required (write tests first, then code)
