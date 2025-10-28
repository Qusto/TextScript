# Feature Specification: Web Frontend with Docker Deployment

**Feature Branch**: `002-web-frontend-docker`
**Created**: 2025-10-27
**Status**: Draft
**Input**: User description: "я бы хотел создать новую фичу, нужно будет завести новую ветку. я хочу сделать простой фронтенд для текущего скрипта, упаковать его в докер и разместить на пром сервере. я создал простую дизайн систему: Философия Дизайна (Design System) Философия остается прежней: Linear/Vercel. Темная тема (zinc), минимум шума, фокус на процессе."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit Article Generation Request (Priority: P1)

A user visits the web interface to generate a styled article. They provide source URLs for style references and a topic, then submit the request to receive a generated article.

**Why this priority**: This is the core functionality - without this, the feature delivers no value. It represents the complete end-to-end user journey from input to output.

**Independent Test**: Can be fully tested by opening the web interface, entering valid inputs (topic and URLs), clicking "Generate", and receiving an article output. Delivers immediate value as a working article generator accessible via web browser.

**Acceptance Scenarios**:

1. **Given** user opens the web interface, **When** they have not entered any inputs, **Then** the "Generate" button is disabled
2. **Given** user enters only a topic "Machine Learning Basics", **When** the URL field is empty, **Then** the "Generate" button remains disabled
3. **Given** user enters only source URLs, **When** the topic field is empty, **Then** the "Generate" button remains disabled
4. **Given** user enters both a topic "Machine Learning Basics" and source URLs "https://example.com/article1", **Then** the "Generate" button becomes enabled
5. **Given** user has filled valid inputs, **When** they click "Generate" button, **Then** the button becomes disabled, shows a loading indicator, all input fields (URL textarea, topic input, research checkbox) become disabled, and the execution card appears immediately showing the "Log" tab
6. **Given** the generation is running, **When** the backend streams log messages, **Then** the log tab displays each message in real-time with auto-scroll to bottom
7. **Given** the generation completes successfully, **When** the final article is ready, **Then** the "Result" tab becomes enabled and displays the generated article text, and all input fields return to enabled state
8. **Given** the result is displayed, **When** user clicks "Copy" button, **Then** the article text is copied to clipboard with a confirmation message
9. **Given** the result is displayed, **When** user clicks "Download .txt" button, **Then** a text file downloads with the article content

---

### User Story 2 - Enable Research Mode (Priority: P2)

A user wants to generate a more comprehensive article by enabling the research option, which triggers additional research steps during generation.

**Why this priority**: This adds value to the core feature by providing enhanced article quality, but the basic generation works without it. It's an enhancement rather than a requirement.

**Independent Test**: Can be tested by checking the "Enable Research" checkbox before generation and verifying that research-related log messages appear and the final article reflects deeper research.

**Acceptance Scenarios**:

1. **Given** user is on the input form, **When** they check the "Enable Research" checkbox, **Then** the checkbox state is reflected visually
2. **Given** research is enabled, **When** user submits the generation request, **Then** the backend receives the research flag and includes research steps in processing
3. **Given** research is running, **When** log messages stream, **Then** research-specific log entries are visible in the log tab
4. **Given** research completes, **When** the article is generated, **Then** the output shows evidence of research integration

---

### User Story 3 - Monitor Generation Progress (Priority: P1)

A user needs to see real-time feedback while their article is being generated to understand what's happening and how long it might take.

**Why this priority**: This is critical for user experience with a long-running process. Without real-time feedback, users would not know if the system is working or stuck.

**Independent Test**: Can be tested by triggering a generation and observing that log messages appear progressively, the interface remains responsive, and the log auto-scrolls.

**Acceptance Scenarios**:

1. **Given** generation is in progress, **When** backend emits log messages, **Then** each message appears in the log tab within 1 second
2. **Given** new log messages appear, **When** the log container receives them, **Then** the view automatically scrolls to show the latest message
3. **Given** the log tab has many messages, **When** the container height exceeds max-height, **Then** a scrollbar appears and auto-scroll continues to work
4. **Given** generation is running, **When** user switches to "Result" tab, **Then** the tab is disabled with visual indication until generation completes

---

### User Story 4 - Handle Generation Errors (Priority: P1)

When something goes wrong during generation (network error, backend crash, invalid input, unreachable URLs), the user needs clear error feedback to understand what happened and try again.

**Why this priority**: Error handling is essential for production readiness. Without it, users face cryptic failures and cannot recover.

**Independent Test**: Can be tested by triggering error conditions (invalid backend, network disconnect, malformed input, unreachable URLs) and verifying error alerts appear with clear messages or warnings appear in logs.

**Acceptance Scenarios**:

1. **Given** generation starts, **When** the backend returns a 500 error, **Then** an error alert appears with the error message instead of the tabs interface
2. **Given** EventSource connection is open, **When** the connection fails or times out, **Then** the error alert displays "Произошла ошибка потока" and the loading state ends
3. **Given** an error occurred, **When** the error alert is displayed, **Then** the generation button and all input fields return to enabled state allowing retry
4. **Given** user sees an error, **When** they correct the issue and click "Generate" again, **Then** the error alert clears and new generation starts
5. **Given** generation is processing source URLs, **When** one URL is unreachable (404, 503, timeout), **Then** a warning message appears in the log tab (e.g., "[WARN] Не удалось получить URL: https://example.com/article1 (Ошибка: Таймаут)") and generation continues with remaining URLs
6. **Given** multiple source URLs are provided, **When** some are unreachable, **Then** the generation completes successfully using only the accessible URLs and displays warning messages for failed ones
7. **Given** user closes the browser tab, **When** the SSE connection is broken during generation, **Then** the backend detects the disconnection and terminates the running script process to prevent resource waste

---

### User Story 5 - Toggle Theme (Priority: P3)

A user can switch between dark and light themes based on their preference, with the interface defaulting to dark theme (zinc palette).

**Why this priority**: This is a nice-to-have feature that improves user comfort but doesn't affect core functionality. The default dark theme is already suitable for most users.

**Independent Test**: Can be tested by clicking the theme toggle button and verifying that the entire interface switches color schemes smoothly.

**Acceptance Scenarios**:

1. **Given** user opens the interface, **When** the page loads, **Then** the dark theme (zinc) is applied by default
2. **Given** user is on the interface, **When** they click the theme toggle button, **Then** the interface switches to light theme with all components updating accordingly
3. **Given** user has selected a theme, **When** they reload the page, **Then** their theme preference persists

---

### User Story 6 - Russian Localization (Priority: P0) 🎯 Critical

A user opens the interface and sees all text elements (labels, buttons, messages, errors) displayed in Russian language for better accessibility to Russian-speaking audience.

**Why this priority**: This is critical for target audience accessibility. The interface must be in Russian to be usable by the intended users. Without localization, users face language barriers.

**Independent Test**: Can be tested by opening the interface and verifying that all UI elements (form labels, buttons, tab names, error messages, placeholders) are in Russian.

**Acceptance Scenarios**:

1. **Given** user opens the interface, **When** the page loads, **Then** all form labels are displayed in Russian ("Название статьи", "Ключевые тезисы", "URL для анализа стиля", "Включить исследование")
2. **Given** user interacts with the form, **When** they hover over buttons or see tooltips, **Then** all button text and tooltips are in Russian ("Сгенерировать", "Копировать", "Скачать .txt")
3. **Given** generation is running, **When** log messages appear, **Then** system messages are in Russian (e.g., "Генерация началась...", "Загружаю URL...", "Создаю статью...")
4. **Given** an error occurs, **When** error alert displays, **Then** the error message is in Russian (e.g., "Произошла ошибка потока", "Не удалось подключиться к серверу")
5. **Given** user completes generation, **When** they view the result tab, **Then** tab labels and success messages are in Russian

---

### User Story 7 - Style Profile Management (Priority: P0) 🎯 Critical

A user can create, view, and manage a style profile extracted from reference URLs. The profile is stored persistently and reused for article generation without re-analyzing URLs each time.

**Why this priority**: This is critical for user workflow efficiency and system architecture. Without profile management, users must provide URLs for every generation, and the system wastes resources re-analyzing the same style repeatedly. Profile persistence enables "set once, use many times" pattern.

**Independent Test**: Can be tested by providing URLs for style extraction, generating a profile, verifying it's saved, then generating articles without re-entering URLs.

**Acceptance Scenarios**:

1. **Given** user opens the interface for the first time, **When** no style profile exists, **Then** the "Стиль" section shows status "Профиль не загружен" with a collapsible URL input field visible
2. **Given** no profile exists, **When** user enters URLs in the style profile section and clicks "Создать профиль", **Then** the system extracts style characteristics from URLs, saves profile to database, and displays status "Профиль загружен"
3. **Given** a profile is loaded, **When** user views the "Стиль" section, **Then** the URL input field is hidden, status shows "Профиль загружен" with green indicator, and a "Посмотреть профиль" button is visible
4. **Given** a profile is loaded, **When** user clicks "Посмотреть профиль", **Then** a modal dialog opens displaying the extracted style characteristics (profile_text from database)
5. **Given** user views the profile, **When** they close the modal, **Then** the profile viewer dialog closes and the form remains in loaded state
6. **Given** a profile is loaded, **When** user clicks "Обновить профиль", **Then** the URL input field becomes visible, allowing user to enter new URLs and create a new profile (replacing the old one)
7. **Given** a profile is loaded, **When** user attempts to generate an article, **Then** the system uses the stored profile_text for generation without requiring URL input
8. **Given** no profile is loaded, **When** user tries to click "Сгенерировать", **Then** the button is disabled and a warning message "Сначала создайте профиль стиля" appears

---

### User Story 8 - Article Title and Key Points (Priority: P1)

A user can specify an article title (required) and optional key points/theses that should be covered in the generated article for better content control.

**Why this priority**: This enhances content control and article relevance. Title field replaces the vague "topic" field with clear article naming. Key points allow users to guide content direction, ensuring the article covers specific theses they care about.

**Independent Test**: Can be tested by entering a title and optional key points, generating an article, and verifying the article reflects the title and covers the specified points.

**Acceptance Scenarios**:

1. **Given** user opens the form, **When** they view the "Контент" accordion section, **Then** they see "Название статьи" input field (required) and "Ключевые тезисы" textarea (optional)
2. **Given** user enters only article title, **When** profile is loaded and they click "Сгенерировать", **Then** generation starts with title, using profile but no key points
3. **Given** user enters article title and key points, **When** they click "Сгенерировать", **Then** generation starts with both title and key points, and the article covers the specified theses
4. **Given** user enters key points without title, **When** they attempt to generate, **Then** the "Сгенерировать" button remains disabled (title is required)
5. **Given** user enters multi-line key points (e.g., "Тезис 1\nТезис 2\nТезис 3"), **When** generation starts, **Then** the backend receives all key points and includes them in the article generation prompt
6. **Given** user generates an article with key points, **When** the article is complete, **Then** the article content reflects and addresses each specified key point

---

### Edge Cases

- **Empty/Long Input**: System prevents submission when topic or URLs are empty (button stays disabled). For extremely long inputs (>10,000 characters), system should either truncate or display validation error.
- **Concurrent Requests**: All input fields and the generate button are disabled during processing, physically preventing a second concurrent request from the same browser session.
- **Backend Crash Mid-Generation**: If the backend process crashes, the SSE connection breaks, triggering the error handler which displays "Произошла ошибка потока" and re-enables the form for retry.
- **Long-Running Generations (30+ minutes)**: System should implement a reasonable timeout (e.g., 10 minutes) and display a timeout error if exceeded, allowing the user to retry.
- **Browser Tab Closed**: Backend detects SSE disconnection and immediately sends SIGTERM/SIGKILL to the running Python process to prevent zombie processes consuming resources.
- **Special Characters/Non-Latin Scripts**: System should handle UTF-8 encoding properly, allowing Cyrillic, Chinese, Arabic, emoji, and special characters in topic input.
- **Unreachable URLs**: Script continues execution when URLs are unreachable (404, 503, timeout), logging warnings like "[WARN] Не удалось получить URL: ... (Ошибка: Таймаут)" without failing the entire generation.
- **Extremely Large Output (>100KB)**: System should handle articles up to 50,000 characters (as per SC-008). Beyond that, consider truncation or streaming the result in chunks.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a web interface with a single-column layout (max-width 3xl) following Linear/Vercel design philosophy
- **FR-002**: System MUST display an input card with three sections: source URLs textarea, topic input field, and research checkbox
- **FR-003**: System MUST validate that topic input is not empty before enabling generation
  - **FR-003.1**: System MUST validate that source URLs textarea is not empty before enabling generation
  - **FR-003.2**: The "Generate" button MUST remain disabled until both topic and source URLs fields are filled with non-empty values
- **FR-004**: System MUST disable the "Generate" button and show a loading indicator immediately upon click
  - **FR-004.1**: When generation is started (isLoading=true), the system MUST disable all input fields (source URLs textarea, topic input field, and research checkbox) in addition to the "Generate" button to prevent concurrent requests
- **FR-005**: System MUST display an execution card with tabs interface immediately when generation starts
- **FR-006**: System MUST stream backend log messages to the frontend in real-time using Server-Sent Events (SSE)
- **FR-007**: System MUST display log messages in a scrollable pre-formatted block with auto-scroll to bottom
- **FR-008**: System MUST keep the "Result" tab disabled until generation completes successfully
- **FR-009**: System MUST enable the "Result" tab and display the final article when generation completes
- **FR-010**: System MUST provide "Copy" and "Download .txt" buttons in the result tab
- **FR-011**: System MUST implement clipboard copy functionality for the generated article
- **FR-012**: System MUST generate a downloadable text file containing the article content
- **FR-013**: System MUST display error alerts (destructive variant) when generation fails or connection errors occur
- **FR-014**: System MUST include a theme toggle in the header allowing users to switch between dark and light themes
- **FR-015**: System MUST default to dark theme using zinc color palette
- **FR-016**: Backend MUST provide a streaming API endpoint that accepts topic, source URLs, and research flag
  - **FR-016.1**: Backend server handler MUST detect SSE connection disconnection (e.g., ClientDisconnect event)
  - **FR-016.2**: Upon detecting disconnection, the server MUST immediately send SIGTERM (or SIGKILL if SIGTERM fails) to the child Python process to prevent zombie processes and resource waste
- **FR-017**: Backend MUST execute the existing article generation script with provided inputs
  - **FR-017.1**: The article generation script MUST NOT fail completely when one or more source URLs are unreachable (404, 503, timeout, DNS error). It MUST continue processing with remaining accessible URLs
- **FR-018**: Backend MUST stream stdout from the script as SSE "message" events
  - **FR-018.1**: When a source URL fails to load, the backend MUST stream a warning message to the log (e.g., "[WARN] Не удалось получить URL: https://example.com/article1 (Ошибка: Таймаут)") and continue execution
- **FR-019**: Backend MUST send the final article as a custom SSE "result" event when successful
- **FR-020**: Backend MUST send error details as a custom SSE "error" event when the script fails
- **FR-021**: Backend MUST send a "close" event when the stream ends
- **FR-022**: System MUST be containerized using Docker with all dependencies included
- **FR-023**: System MUST be deployable to a production server
- **FR-024**: Frontend MUST use shadcn/ui components (button, card, input, textarea, label, checkbox, alert, tabs)
- **FR-025**: Frontend MUST implement responsive design working on desktop and tablet viewports
- **FR-026**: System MUST display all UI text elements in Russian language (labels, buttons, messages, errors, placeholders)
- **FR-027**: System MUST provide i18n translation dictionary for all interface strings
- **FR-028**: System MUST persist style profiles in SQLite database with schema: id, urls_hash, profile_text, source_urls, created_at, updated_at
- **FR-029**: Backend MUST provide API endpoints for style profile management: GET /api/profiles/current, POST /api/profiles, GET /api/profiles/{id}, DELETE /api/profiles/{id}
- **FR-030**: System MUST extract style characteristics from provided URLs and save as profile_text in database
- **FR-031**: System MUST display style profile status indicator (loaded/not loaded) in the form
- **FR-032**: System MUST allow users to view stored profile_text in a modal dialog
- **FR-033**: System MUST allow users to update style profile by providing new URLs (replaces existing profile)
- **FR-034**: System MUST disable article generation button when no style profile is loaded (with warning message)
- **FR-035**: System MUST require article title field (cannot be empty) for article generation
- **FR-036**: System MUST accept optional key points/theses field (multiline textarea) for article generation
- **FR-037**: Backend MUST integrate key points into article generation prompt when provided
- **FR-038**: Frontend MUST organize form inputs using accordion pattern with three sections: "Контент" (title, keyPoints), "Стиль" (profile management), "Настройки" (research checkbox)
- **FR-039**: System MUST optimize interface compactness for 1280x720 viewport (reduce padding, adjust spacing)
- **FR-040**: System MUST implement two-stage research mode: Stage 1 - information collection via research API, Stage 2 - article generation with collected data
- **FR-041**: Backend MUST change API contract from GET /api/generate?topic=...&source_urls=... to POST /api/generate with JSON body {title, keyPoints, profileId, enableResearch}
- **FR-042**: Backend SSE streaming MUST send JSON format messages: `data: {"type":"log|result|error","message":"..."}\n\n` instead of plain text format

### Key Entities

- **Generation Request**: Represents a single article generation job with title (string, required), key points (string, optional), profile ID (integer, required), and research flag (boolean)
- **Style Profile**: Represents extracted writing style characteristics with id, urls_hash (MD5), profile_text (LLM analysis), source_urls (JSON array), created_at, updated_at timestamps
- **Log Message**: Represents a single line of output from the generation process with type ("log" | "result" | "error") and message text
- **Generated Article**: Represents the final output with article text content and generation metadata (completion time, research enabled, title, key points used)
- **User Session**: Represents a browser session with theme preference, active generation state, and loaded style profile ID
- **Research Result**: Represents collected information from research API with facts, statistics, quotes, sources used for article enrichment (two-stage generation)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a generation request and see the first log message appear within 2 seconds
- **SC-002**: Log messages appear in real-time with less than 500ms delay from backend emission
- **SC-003**: The interface remains responsive during generation with no UI freezing or lag
- **SC-004**: Users can successfully copy the generated article to clipboard in one click
- **SC-005**: Users can download the article as a .txt file in one click
- **SC-006**: Error conditions display clear, user-friendly error messages within 2 seconds of occurrence
- **SC-007**: The application successfully deploys to production and remains accessible with 99% uptime
- **SC-008**: The system handles articles up to 50,000 characters without performance degradation
- **SC-009**: Theme toggle switches appearance in under 200ms with no visual glitches
- **SC-010**: The Docker container starts successfully in under 30 seconds with all services ready
- **SC-011**: When one or more source URLs are unreachable, the system completes generation successfully with remaining URLs and displays clear warning messages for failed URLs
- **SC-012**: When a user closes the browser tab during generation, the backend process terminates within 5 seconds, freeing all resources
- **SC-013**: Users cannot trigger concurrent generation requests - the interface prevents multiple submissions through form field disabling
- **SC-014**: All UI text elements (labels, buttons, messages, errors) are displayed in Russian without English fallbacks
- **SC-015**: Style profile creation completes within 30 seconds for 1-3 reference URLs
- **SC-016**: Users can view their stored style profile characteristics in under 1 second (database query + modal render)
- **SC-017**: The "Сгенерировать" button is disabled with clear warning message when no style profile is loaded
- **SC-018**: Interface fits comfortably in 1280x720 viewport without vertical scroll on form (before generation starts)
- **SC-019**: Key points (if provided) are successfully incorporated into generated article content
- **SC-020**: Two-stage research mode completes information collection before starting article generation, with clear log separation between stages
