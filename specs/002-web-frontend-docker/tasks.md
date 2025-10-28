# Tasks: Web Frontend with Docker Deployment

**Input**: Design documents from `/specs/002-web-frontend-docker/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-spec.yaml, quickstart.md

**Tests**: Tests are OPTIONAL - only included if explicitly requested. This feature specification does NOT request TDD, so implementation tasks only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3) - only for user story phases
- Include exact file paths in descriptions

## Path Conventions

This is a web app with:
- `web-frontend/` - Next.js frontend (CLIENT ONLY - NO API ROUTES)
- `backend/` - FastAPI backend
- `src/` - Existing Python article script (minimal changes)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

**Agent**: `frontend-developer` (T001-T008), `python-backend-developer` (T009-T012)

- [X] T001 Create web-frontend/ directory and initialize Next.js 14 project with TypeScript and App Router
- [X] T002 [P] Install and configure Tailwind CSS in web-frontend/tailwind.config.ts
- [X] T003 [P] Initialize shadcn/ui in web-frontend/ with zinc color palette (dark theme default)
- [X] T004 [P] Install shadcn/ui components: button, card, input, textarea, label, checkbox, alert, tabs in web-frontend/
- [X] T005 [P] Install additional dependencies: next-themes, lucide-react in web-frontend/
- [X] T006 [P] Create web-frontend/.env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
- [X] T007 [P] Setup web-frontend/src/lib/utils.ts with cn() helper function
- [X] T008 [P] Create web-frontend/src/app/layout.tsx with ThemeProvider wrapper
- [X] T009 Create backend/ directory structure: src/api/, src/services/, tests/
- [X] T010 [P] Create backend/pyproject.toml with FastAPI, uvicorn, pytest dependencies
- [X] T011 [P] Run poetry install in backend/
- [X] T012 [P] Create backend/src/main.py with FastAPI app initialization and CORS middleware

**Checkpoint**: Project structure ready - foundational components can now be implemented

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Agent**: `python-backend-developer` (T013-T020)

### Backend Foundation

- [X] T013 Create backend/src/services/process_manager.py with ProcessTracker dataclass (FR-016.2)
- [X] T014 Implement ProcessManager class in backend/src/services/process_manager.py with active_processes dict tracking
- [X] T015 Implement cleanup_process() method in backend/src/services/process_manager.py with SIGTERM → SIGKILL logic (3s timeout)
- [X] T016 Implement track_process() context manager in backend/src/services/process_manager.py for automatic cleanup on disconnect
- [X] T017 Create backend/src/api/generate.py with FastAPI router and SSE streaming endpoint skeleton (FR-016)
- [X] T018 Implement subprocess spawning in backend/src/api/generate.py using asyncio.create_subprocess_exec (FR-017)
- [X] T019 Implement stdout streaming loop in backend/src/api/generate.py that yields SSE data: messages (FR-018)
- [X] T020 Add client disconnect detection in backend/src/api/generate.py using request.is_disconnected() (FR-016.1)

**Checkpoint**: Backend API ready - frontend can now integrate with SSE streaming

---

## Phase 3: User Story 1 - Submit Article Generation Request (Priority: P1) 🎯 MVP

**Goal**: Core end-to-end functionality - user can enter topic and URLs, click generate, and receive an article

**Independent Test**: Open web interface, enter topic "Test Article" and URL "https://example.com", click "Generate", verify article appears in Result tab

**Agent**: `frontend-developer` (T021-T029), `python-backend-developer` (T030-T032)

### Frontend Implementation for US1

- [ ] T021 [P] [US1] Create web-frontend/src/components/input-form.tsx with Card, Input, Textarea, Checkbox, Button components (FR-002)
- [ ] T022 [US1] Implement topic and sourceUrls state management in web-frontend/src/components/input-form.tsx with useState
- [ ] T023 [US1] Implement button disabled logic in web-frontend/src/components/input-form.tsx: disabled when topic OR sourceUrls empty (FR-003, FR-003.1, FR-003.2)
- [ ] T024 [US1] Implement onSubmit handler in web-frontend/src/components/input-form.tsx that passes data to parent callback (FR-004)
- [ ] T025 [US1] Add disabled state for all input fields (topic, sourceUrls, research checkbox) in web-frontend/src/components/input-form.tsx when isLoading=true (FR-004.1)
- [ ] T026 [P] [US1] Create web-frontend/src/components/execution-view.tsx with Tabs component (log tab and result tab) (FR-005)
- [ ] T027 [US1] Implement log display in web-frontend/src/components/execution-view.tsx with pre-formatted scrollable block and auto-scroll to bottom (FR-007)
- [ ] T028 [US1] Implement result tab in web-frontend/src/components/execution-view.tsx with disabled state until finalArticle is set (FR-008, FR-009)
- [ ] T029 [US1] Add Copy and Download buttons in result tab of web-frontend/src/components/execution-view.tsx (FR-010)

### Backend Implementation for US1

- [ ] T030 [US1] Implement result event emission in backend/src/api/generate.py: read output.txt and send event: result (FR-019)
- [ ] T031 [US1] Implement close event emission in backend/src/api/generate.py after successful completion (FR-021)
- [ ] T032 [US1] Add input validation in backend/src/api/generate.py for topic (min 1 char, max 1000) and source_urls (valid URLs, 1-10 count)

### Frontend Integration for US1

- [ ] T033 [US1] Create web-frontend/src/app/page.tsx with state: isLoading, logLines[], finalArticle, error (DM-5)
- [ ] T034 [US1] Implement handleSubmit in web-frontend/src/app/page.tsx: create EventSource with /api/generate?topic=...&source_urls=...&research=... (FR-006)
- [ ] T035 [US1] Implement EventSource message handler in web-frontend/src/app/page.tsx: append to logLines array
- [ ] T036 [US1] Implement EventSource result handler in web-frontend/src/app/page.tsx: set finalArticle and isLoading=false
- [ ] T037 [US1] Implement EventSource close handler in web-frontend/src/app/page.tsx: close EventSource connection
- [ ] T038 [US1] Implement clipboard copy functionality in web-frontend/src/components/execution-view.tsx using navigator.clipboard.writeText() (FR-011)
- [ ] T039 [US1] Implement download functionality in web-frontend/src/components/execution-view.tsx: create Blob and download as .txt file (FR-012)
- [ ] T040 [US1] Add layout and styling in web-frontend/src/app/page.tsx: single-column max-w-3xl container with dark zinc theme (FR-001, FR-015)

**Checkpoint**: MVP complete - user can generate articles end-to-end

---

## Phase 4: User Story 2 - Enable Research Mode (Priority: P2)

**Goal**: User can check "Enable Research" checkbox to trigger deeper research during generation

**Independent Test**: Check "Enable Research" before generation, verify research-related log messages appear in log tab

**Agent**: `python-backend-developer` (T041), `frontend-developer` (T042)

- [ ] T041 [US2] Add research query parameter handling in backend/src/api/generate.py and pass --research flag to subprocess (FR-016)
- [ ] T042 [US2] Add research checkbox state in web-frontend/src/components/input-form.tsx and include in EventSource URL query params

**Checkpoint**: Research mode functional - generates enhanced articles

---

## Phase 5: User Story 3 - Monitor Generation Progress (Priority: P1)

**Goal**: User sees real-time log messages streaming during generation with auto-scroll

**Independent Test**: Trigger generation, verify log messages appear progressively within 1 second, view auto-scrolls to latest message

**Agent**: `frontend-developer` (T043-T045)

- [ ] T043 [US3] Implement useRef for logEndRef in web-frontend/src/components/execution-view.tsx for scroll anchor
- [ ] T044 [US3] Implement useEffect with logLines dependency in web-frontend/src/components/execution-view.tsx to auto-scroll with scrollIntoView({ behavior: 'smooth' })
- [ ] T045 [US3] Add max-height and overflow-y-auto classes to log container in web-frontend/src/components/execution-view.tsx for scrollbar appearance

**Checkpoint**: Real-time progress monitoring working with smooth auto-scroll

---

## Phase 6: User Story 4 - Handle Generation Errors (Priority: P1)

**Goal**: Clear error feedback when generation fails (backend crash, network error, unreachable URLs)

**Independent Test**: Trigger error conditions (invalid backend URL, network disconnect, unreachable source URLs), verify error alerts or warnings appear

**Agent**: `python-backend-developer` (T046-T048), `frontend-developer` (T049-T052)

### Backend Error Handling for US4

- [ ] T046 [P] [US4] Implement graceful URL failure handling in backend/src/api/generate.py: wrap URL fetch in try-except, log [WARN] for failures, continue with remaining URLs (FR-017.1, FR-018.1)
- [ ] T047 [P] [US4] Implement error event emission in backend/src/api/generate.py: send event: error with error_type and message when script fails (FR-020)
- [ ] T048 [US4] Add 400 validation error responses in backend/src/api/generate.py for invalid input (empty topic, bad URL format)

### Frontend Error Handling for US4

- [ ] T049 [P] [US4] Create web-frontend/src/components/ui/alert.tsx for error display (destructive variant) (FR-013)
- [ ] T050 [US4] Implement EventSource error handler in web-frontend/src/app/page.tsx: set error state and isLoading=false
- [ ] T051 [US4] Implement EventSource custom error event handler in web-frontend/src/app/page.tsx: display error alert instead of tabs
- [ ] T052 [US4] Add error state reset in web-frontend/src/app/page.tsx when starting new generation (clear previous error)

**Checkpoint**: Error handling complete - graceful degradation for unreachable URLs, clear error messages

---

## Phase 7: User Story 5 - Toggle Theme (Priority: P3)

**Goal**: User can switch between dark and light themes with persistence

**Independent Test**: Click theme toggle button, verify interface switches color schemes, reload page and verify theme persists

**Agent**: `frontend-developer` (T053-T055)

- [ ] T053 [P] [US5] Create web-frontend/src/components/theme-toggle.tsx with button using next-themes useTheme hook (FR-014)
- [ ] T054 [P] [US5] Add sun/moon icons from lucide-react in web-frontend/src/components/theme-toggle.tsx for visual indication
- [ ] T055 [US5] Add ThemeToggle component to header in web-frontend/src/app/page.tsx

**Checkpoint**: Theme toggle complete - user can switch themes with localStorage persistence

---

## Phase 8: Docker Deployment (Priority: P1)

**Goal**: Entire application deployable to production via Docker Compose

**Independent Test**: Run `docker-compose up --build`, verify frontend at http://localhost:3000, backend at http://localhost:8000, generate test article end-to-end

**Agent**: `production-deployment` (T056-T065)

### Docker Configuration

- [ ] T056 [P] Create web-frontend/Dockerfile with multi-stage build (deps, builder, runner stages) targeting node:20-alpine (FR-022)
- [ ] T057 [P] Create backend/Dockerfile with multi-stage build (deps, runtime stages) targeting python:3.11-slim (FR-022)
- [ ] T058 [P] Create .dockerignore in repository root with patterns for node_modules, .git, __pycache__, .next
- [ ] T059 Create docker-compose.yml in repository root with services: frontend (port 3000), backend (port 8000)
- [ ] T060 Configure frontend service in docker-compose.yml with environment: NEXT_PUBLIC_API_URL=http://backend:8000
- [ ] T061 Configure backend service in docker-compose.yml with volumes for src/ (existing script access)
- [ ] T062 Add shared network in docker-compose.yml for frontend-backend communication
- [ ] T063 Test docker-compose build: run `docker-compose build` from repository root
- [ ] T064 Test docker-compose startup: run `docker-compose up` and verify services start within 30 seconds (SC-010)
- [ ] T065 Test end-to-end article generation via Docker: open http://localhost:3000, submit generation, verify result

### Production Deployment

- [ ] T066 Create deployment documentation in specs/002-web-frontend-docker/quickstart.md for production server setup (FR-023)
- [ ] T067 Add health check endpoint GET /health in backend/src/main.py returning {"status": "healthy", "active_processes": count}
- [ ] T068 Configure health checks in docker-compose.yml for both frontend and backend services
- [ ] T069 Test health checks: curl http://localhost:8000/health and http://localhost:3000 after docker-compose up

**Checkpoint**: Docker deployment complete - application fully containerized and production-ready

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**Agent**: `frontend-developer` (T070-T072), `python-backend-developer` (T073-T075)

- [ ] T070 [P] Add responsive design adjustments in web-frontend/src/app/globals.css for tablet viewports (FR-025)
- [ ] T071 [P] Add loading spinner component in web-frontend/src/components/input-form.tsx when isLoading=true (FR-004)
- [ ] T072 [P] Add confirmation message for clipboard copy in web-frontend/src/components/execution-view.tsx using toast or alert (SC-004)
- [ ] T073 [P] Add request timeout handling in backend/src/api/generate.py: terminate process after 10 minutes (edge case: long-running generations)
- [ ] T074 [P] Add logging for process lifecycle events in backend/src/services/process_manager.py (start, cleanup, disconnect)
- [ ] T075 [P] Add max article length validation in backend/src/api/generate.py: enforce 50,000 character limit (SC-008)
- [ ] T076 Update CLAUDE.md in repository root to include Next.js 14, FastAPI, Docker Compose technologies
- [ ] T077 Run quickstart.md validation: follow all setup steps from specs/002-web-frontend-docker/quickstart.md
- [ ] T078 Add AICODE comments to key technical decisions across web-frontend/src/ and backend/src/ files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - **US1 (Phase 3)**: Can start after Phase 2 - No dependencies on other stories (MVP - DO THIS FIRST)
  - **US2 (Phase 4)**: Can start after Phase 2 - Independent of other stories
  - **US3 (Phase 5)**: Can start after US1 T027 (log display exists) - Minor integration with US1
  - **US4 (Phase 6)**: Can start after Phase 2 - Independent error handling
  - **US5 (Phase 7)**: Can start after Phase 1 - Completely independent
- **Docker Deployment (Phase 8)**: Depends on US1 completion (MVP must work) - Recommended after US1, US3, US4 complete
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Priorities

**Recommended Implementation Order**:
1. **Phase 1 + 2**: Setup + Foundational (REQUIRED)
2. **Phase 3 (US1)**: Submit Article Generation Request (P1 - MVP) ⭐
3. **Phase 5 (US3)**: Monitor Generation Progress (P1 - Critical UX) ⭐
4. **Phase 6 (US4)**: Handle Generation Errors (P1 - Production readiness) ⭐
5. **Phase 8**: Docker Deployment (Deploy MVP to production)
6. **Phase 4 (US2)**: Enable Research Mode (P2 - Enhancement)
7. **Phase 7 (US5)**: Toggle Theme (P3 - Nice-to-have)
8. **Phase 9**: Polish

**Minimum Viable Product (MVP)**: Phase 1 + 2 + 3 (US1) = Working article generator

### Within Each User Story

- Frontend tasks can run in parallel with backend tasks (marked [P]) when working on different files
- Within frontend: UI components before integration (e.g., T021-T029 before T033-T040)
- Within backend: ProcessManager before API endpoint (e.g., T013-T016 before T017-T020)
- Integration tasks depend on component tasks completing

### Parallel Opportunities by Agent

**Frontend Developer (can work in parallel with backend)**:
- Phase 1: T001-T008 (all [P] after T001)
- Phase 3 (US1): T021, T026 (different files)
- Phase 4 (US2): T042 (independent checkbox)
- Phase 5 (US3): T043-T045 (sequential within US3)
- Phase 6 (US4): T049, T050-T052 (T049 parallel, T050-T052 sequential)
- Phase 7 (US5): T053-T054 (parallel), T055 (integration)

**Backend Developer (can work in parallel with frontend)**:
- Phase 1: T009-T012 (all [P] after T009)
- Phase 2: T013-T016 (sequential), T017-T020 (sequential after T016)
- Phase 3 (US1): T030-T032 (sequential)
- Phase 4 (US2): T041 (independent)
- Phase 6 (US4): T046-T047 (parallel), T048 (sequential)

**Deployment (depends on both frontend + backend)**:
- Phase 8: T056-T058 (all [P]), T059-T069 (mostly sequential for testing)

---

## Parallel Example: Foundational Phase (Phase 2)

```bash
# Backend developer works on ProcessManager and SSE endpoint:
# Sequential execution required:
Task T013: Create ProcessTracker dataclass
Task T014: Implement ProcessManager class
Task T015: Implement cleanup_process() method
Task T016: Implement track_process() context manager
Task T017: Create SSE streaming endpoint skeleton
Task T018: Implement subprocess spawning
Task T019: Implement stdout streaming loop
Task T020: Add client disconnect detection
```

## Parallel Example: User Story 1 (Phase 3)

```bash
# Frontend developer and backend developer can work in parallel:

# Frontend Developer:
Task T021 [P]: Create input-form.tsx component
Task T026 [P]: Create execution-view.tsx component (parallel with T021)
# Then sequentially: T022-T025 (input form logic)
# Then sequentially: T027-T029 (execution view logic)
# Then sequentially: T033-T040 (page integration)

# Backend Developer (parallel with frontend):
Task T030: Implement result event emission
Task T031: Implement close event emission
Task T032: Add input validation

# Both complete → US1 integration ready
```

## Parallel Example: Docker Deployment (Phase 8)

```bash
# Deployment engineer can parallelize Docker configs:
Task T056 [P]: Create web-frontend/Dockerfile
Task T057 [P]: Create backend/Dockerfile
Task T058 [P]: Create .dockerignore

# Then sequential for orchestration and testing:
Task T059: Create docker-compose.yml
Task T060-T062: Configure services
Task T063-T065: Test builds and startup
Task T066-T069: Add production docs and health checks
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Fastest path to working product**:

1. Complete Phase 1: Setup (~2 hours)
2. Complete Phase 2: Foundational (~4 hours) - CRITICAL
3. Complete Phase 3: User Story 1 (~6 hours)
4. **STOP and VALIDATE**: Test article generation end-to-end
5. Optional: Add Phase 5 (US3) for better UX (~1 hour)
6. Optional: Add Phase 6 (US4) for error handling (~2 hours)
7. Complete Phase 8: Docker deployment (~3 hours)
8. Deploy to production

**Total MVP time**: ~15-18 hours (with US1 + US3 + US4 + Docker)

### Incremental Delivery

**Staged rollout strategy**:

1. **Milestone 1**: Setup + Foundational → Foundation ready (~6 hours)
2. **Milestone 2**: + US1 → MVP deployed (~12 hours total) 🎯
3. **Milestone 3**: + US3 + US4 → Production-ready (~16 hours total)
4. **Milestone 4**: + Docker → Containerized deployment (~19 hours total)
5. **Milestone 5**: + US2 + US5 → Feature-complete (~22 hours total)
6. **Milestone 6**: + Polish → Polished release (~24 hours total)

Each milestone adds value without breaking previous functionality.

### Parallel Team Strategy

**With 2 developers (frontend + backend)**:

1. **Together**: Complete Phase 1 Setup (~2 hours)
2. **Backend Dev**: Complete Phase 2 Foundational (~4 hours) - CRITICAL PATH
3. **Frontend Dev (parallel with step 2)**: Start Phase 3 frontend tasks using mock API (~3 hours)
4. **Together**: Integrate frontend + backend for Phase 3 US1 (~2 hours)
5. **Frontend Dev**: Phase 5 US3 + Phase 7 US5 (~2 hours)
6. **Backend Dev**: Phase 4 US2 + Phase 6 US4 (~3 hours)
7. **Deployment**: Phase 8 Docker (~3 hours)
8. **Together**: Phase 9 Polish (~2 hours)

**Total parallel time**: ~16-18 hours (vs 24 hours sequential)

**With 3 developers (frontend + backend + deployment)**:

- Deployment engineer can prepare Docker configs (Phase 8) while others work on US1-US5
- Reduces total time to ~14-16 hours

---

## Agent Assignment Summary

### Tasks by Agent

**frontend-developer** (40 tasks):
- Phase 1 Setup: T001-T008 (8 tasks)
- Phase 3 US1 Frontend: T021-T029, T033-T040 (18 tasks)
- Phase 4 US2 Frontend: T042 (1 task)
- Phase 5 US3: T043-T045 (3 tasks)
- Phase 6 US4 Frontend: T049-T052 (4 tasks)
- Phase 7 US5: T053-T055 (3 tasks)
- Phase 9 Polish: T070-T072 (3 tasks)

**python-backend-developer** (28 tasks):
- Phase 1 Setup: T009-T012 (4 tasks)
- Phase 2 Foundational: T013-T020 (8 tasks)
- Phase 3 US1 Backend: T030-T032 (3 tasks)
- Phase 4 US2 Backend: T041 (1 task)
- Phase 6 US4 Backend: T046-T048 (3 tasks)
- Phase 8 Deployment: T067 (1 task - health endpoint)
- Phase 9 Polish: T073-T075 (3 tasks)

**production-deployment** (14 tasks):
- Phase 8 Docker: T056-T069 (14 tasks)

**Any agent** (4 tasks):
- Phase 9 Polish: T076-T078 (3 tasks - documentation and validation)

**Total**: 78 tasks

---

## Notes

- **[P] tasks**: Different files, no dependencies on same-file modifications
- **[Story] label**: Maps task to specific user story from spec.md for traceability
- **Agent assignment**: Based on plan.md Agent Assignment Strategy section
- **AICODE comments**: Should be added to key decisions throughout implementation (T078)
- **MVP scope**: Phase 1 + 2 + 3 (US1) = 32 tasks for working article generator
- **Production-ready scope**: Add Phase 5 (US3) + Phase 6 (US4) + Phase 8 (Docker) = 59 tasks
- **Feature-complete scope**: All phases = 78 tasks
- **No tests included**: Feature spec does not request TDD approach
- **Commit frequency**: Commit after each task or logical group of parallel tasks
- **Checkpoints**: Stop at any user story checkpoint to validate independently
- **Critical path**: Phase 2 (Foundational) blocks all user stories - highest priority
- **Next.js API Routes**: Do NOT use app/api/ directory - frontend connects directly to FastAPI backend (see plan.md AICODE-NOTE)
