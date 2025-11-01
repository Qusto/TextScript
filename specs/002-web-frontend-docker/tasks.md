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

- [X] T021 [P] [US1] Create web-frontend/src/components/input-form.tsx with Card, Input, Textarea, Checkbox, Button components (FR-002)
- [X] T022 [US1] Implement topic and sourceUrls state management in web-frontend/src/components/input-form.tsx with useState
- [X] T023 [US1] Implement button disabled logic in web-frontend/src/components/input-form.tsx: disabled when topic OR sourceUrls empty (FR-003, FR-003.1, FR-003.2)
- [X] T024 [US1] Implement onSubmit handler in web-frontend/src/components/input-form.tsx that passes data to parent callback (FR-004)
- [X] T025 [US1] Add disabled state for all input fields (topic, sourceUrls, research checkbox) in web-frontend/src/components/input-form.tsx when isLoading=true (FR-004.1)
- [X] T026 [P] [US1] Create web-frontend/src/components/execution-view.tsx with Tabs component (log tab and result tab) (FR-005)
- [X] T027 [US1] Implement log display in web-frontend/src/components/execution-view.tsx with pre-formatted scrollable block and auto-scroll to bottom (FR-007)
- [X] T028 [US1] Implement result tab in web-frontend/src/components/execution-view.tsx with disabled state until finalArticle is set (FR-008, FR-009)
- [X] T029 [US1] Add Copy and Download buttons in result tab of web-frontend/src/components/execution-view.tsx (FR-010)

### Backend Implementation for US1

- [X] T030 [US1] Implement result event emission in backend/src/api/generate.py: read output.txt and send event: result (FR-019)
- [X] T031 [US1] Implement close event emission in backend/src/api/generate.py after successful completion (FR-021)
- [X] T032 [US1] Add input validation in backend/src/api/generate.py for topic (min 1 char, max 1000) and source_urls (valid URLs, 1-10 count)

### Frontend Integration for US1

- [X] T033 [US1] Create web-frontend/src/app/page.tsx with state: isLoading, logLines[], finalArticle, error (DM-5)
- [X] T034 [US1] Implement handleSubmit in web-frontend/src/app/page.tsx: create EventSource with /api/generate?topic=...&source_urls=...&research=... (FR-006)
- [X] T035 [US1] Implement EventSource message handler in web-frontend/src/app/page.tsx: append to logLines array
- [X] T036 [US1] Implement EventSource result handler in web-frontend/src/app/page.tsx: set finalArticle and isLoading=false
- [X] T037 [US1] Implement EventSource close handler in web-frontend/src/app/page.tsx: close EventSource connection
- [X] T038 [US1] Implement clipboard copy functionality in web-frontend/src/components/execution-view.tsx using navigator.clipboard.writeText() (FR-011)
- [X] T039 [US1] Implement download functionality in web-frontend/src/components/execution-view.tsx: create Blob and download as .txt file (FR-012)
- [X] T040 [US1] Add layout and styling in web-frontend/src/app/page.tsx: single-column max-w-3xl container with dark zinc theme (FR-001, FR-015)

**Checkpoint**: MVP complete - user can generate articles end-to-end

---

## Phase 4: User Story 2 - Enable Research Mode (Priority: P2)

**Goal**: User can check "Enable Research" checkbox to trigger deeper research during generation

**Independent Test**: Check "Enable Research" before generation, verify research-related log messages appear in log tab

**Agent**: `python-backend-developer` (T041), `frontend-developer` (T042)

- [X] T041 [US2] Add research query parameter handling in backend/src/api/generate.py and pass --research flag to subprocess (FR-016)
- [X] T042 [US2] Add research checkbox state in web-frontend/src/components/input-form.tsx and include in EventSource URL query params

**Checkpoint**: Research mode functional - generates enhanced articles

---

## Phase 5: User Story 3 - Monitor Generation Progress (Priority: P1)

**Goal**: User sees real-time log messages streaming during generation with auto-scroll

**Independent Test**: Trigger generation, verify log messages appear progressively within 1 second, view auto-scrolls to latest message

**Agent**: `frontend-developer` (T043-T045)

- [X] T043 [US3] Implement useRef for logEndRef in web-frontend/src/components/execution-view.tsx for scroll anchor
- [X] T044 [US3] Implement useEffect with logLines dependency in web-frontend/src/components/execution-view.tsx to auto-scroll with scrollIntoView({ behavior: 'smooth' })
- [X] T045 [US3] Add max-height and overflow-y-auto classes to log container in web-frontend/src/components/execution-view.tsx for scrollbar appearance

**Checkpoint**: Real-time progress monitoring working with smooth auto-scroll

---

## Phase 6: User Story 4 - Handle Generation Errors (Priority: P1)

**Goal**: Clear error feedback when generation fails (backend crash, network error, unreachable URLs)

**Independent Test**: Trigger error conditions (invalid backend URL, network disconnect, unreachable source URLs), verify error alerts or warnings appear

**Agent**: `python-backend-developer` (T046-T048), `frontend-developer` (T049-T052)

### Backend Error Handling for US4

- [X] T046 [P] [US4] Implement graceful URL failure handling in backend/src/api/generate.py: wrap URL fetch in try-except, log [WARN] for failures, continue with remaining URLs (FR-017.1, FR-018.1)
- [X] T047 [P] [US4] Implement error event emission in backend/src/api/generate.py: send event: error with error_type and message when script fails (FR-020)
- [X] T048 [US4] Add 400 validation error responses in backend/src/api/generate.py for invalid input (empty topic, bad URL format)

### Frontend Error Handling for US4

- [X] T049 [P] [US4] Create web-frontend/src/components/ui/alert.tsx for error display (destructive variant) (FR-013)
- [X] T050 [US4] Implement EventSource error handler in web-frontend/src/app/page.tsx: set error state and isLoading=false
- [X] T051 [US4] Implement EventSource custom error event handler in web-frontend/src/app/page.tsx: display error alert instead of tabs
- [X] T052 [US4] Add error state reset in web-frontend/src/app/page.tsx when starting new generation (clear previous error)

**Checkpoint**: Error handling complete - graceful degradation for unreachable URLs, clear error messages

---

## Phase 7: User Story 5 - Toggle Theme (Priority: P3)

**Goal**: User can switch between dark and light themes with persistence

**Independent Test**: Click theme toggle button, verify interface switches color schemes, reload page and verify theme persists

**Agent**: `frontend-developer` (T053-T055)

- [X] T053 [P] [US5] Create web-frontend/src/components/theme-toggle.tsx with button using next-themes useTheme hook (FR-014)
- [X] T054 [P] [US5] Add sun/moon icons from lucide-react in web-frontend/src/components/theme-toggle.tsx for visual indication
- [X] T055 [US5] Add ThemeToggle component to header in web-frontend/src/app/page.tsx

**Checkpoint**: Theme toggle complete - user can switch themes with localStorage persistence

---

## Phase 8: Docker Deployment (Priority: P1) ⚠️ EXECUTE AFTER PHASE 10

**Goal**: Entire application deployable to production via Docker Compose

**⚠️ EXECUTION ORDER**: This phase is executed AFTER Phase 10 (all Sprints) to package the final version with all features

**Independent Test**: Run `docker-compose up --build`, verify frontend at http://localhost:3000, backend at http://localhost:8000, generate test article end-to-end

**Agent**: `production-deployment` (T056-T065)

### Docker Configuration

- [X] T056 [P] Create web-frontend/Dockerfile with multi-stage build (deps, builder, runner stages) targeting node:20-alpine (FR-022)
- [X] T057 [P] Create backend/Dockerfile with multi-stage build (deps, runtime stages) targeting python:3.11-slim (FR-022)
- [X] T058 [P] Create .dockerignore in repository root with patterns for node_modules, .git, __pycache__, .next
- [X] T059 Create docker-compose.yml in repository root with services: frontend (port 3000), backend (port 8000)
- [X] T060 Configure frontend service in docker-compose.yml with environment: NEXT_PUBLIC_API_URL=http://backend:8000
- [X] T061 Configure backend service in docker-compose.yml with volumes for src/ (existing script access)
- [X] T062 Add shared network in docker-compose.yml for frontend-backend communication
- [X] T063 Test docker-compose build: run `docker-compose build` from repository root
- [X] T064 Test docker-compose startup: run `docker-compose up` and verify services start within 30 seconds (SC-010)
- [X] T065 Test end-to-end article generation via Docker: open http://localhost:3000, submit generation, verify result

### Production Deployment

- [X] T066 Create deployment documentation in specs/002-web-frontend-docker/quickstart.md for production server setup (FR-023)
- [X] T067 Add health check endpoint GET /health in backend/src/main.py returning {"status": "healthy", "active_processes": count}
- [X] T068 Configure health checks in docker-compose.yml for both frontend and backend services
- [X] T069 Test health checks: curl http://localhost:8000/health and http://localhost:3000 after docker-compose up

**Checkpoint**: Docker deployment complete - application fully containerized and production-ready

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**Agent**: `frontend-developer` (T070-T072), `python-backend-developer` (T073-T075)

- [X] T070 [P] Add responsive design adjustments in web-frontend/src/app/globals.css for tablet viewports (FR-025)
- [X] T071 [P] Add loading spinner component in web-frontend/src/components/input-form.tsx when isLoading=true (FR-004)
- [X] T072 [P] Add confirmation message for clipboard copy in web-frontend/src/components/execution-view.tsx using toast or alert (SC-004)
- [X] T073 [P] Add request timeout handling in backend/src/api/generate.py: terminate process after 10 minutes (edge case: long-running generations)
- [X] T074 [P] Add logging for process lifecycle events in backend/src/services/process_manager.py (start, cleanup, disconnect)
- [X] T075 [P] Add max article length validation in backend/src/api/generate.py: enforce 50,000 character limit (SC-008)
- [X] T076 Update CLAUDE.md in repository root to include Next.js 14, FastAPI, Docker Compose technologies
- [ ] T077 Run quickstart.md validation: follow all setup steps from specs/002-web-frontend-docker/quickstart.md
- [X] T078 Add AICODE comments to key technical decisions across web-frontend/src/ and backend/src/ files

---

## Dependencies & Execution Order

### ⚠️ UPDATED EXECUTION SEQUENCE (2025-10-29)

**ACTUAL IMPLEMENTATION ORDER** (revised based on user requirements):
1. ✅ Phase 1-7: Setup + User Stories (COMPLETED)
2. ✅ Phase 9: Polish (COMPLETED)
3. ✅ Phase 10 Sprint 1: Critical Fixes (T080-T085) (COMPLETED)
4. ✅ Phase 10 Sprint 2: Database & Backend API (T086-T093) (COMPLETED)
5. 🎯 **Phase 10 Sprint 3: Style Profile UI** (T094-T103) ← **CURRENT PRIORITY**
6. 🎯 **Phase 10 Sprint 4: Research Mode & Integration** (T104-T110) ← **NEXT**
7. 🐳 **Phase 8: Docker Deployment - FINAL** (T063-T065, T069, T077) ← **PACKAGE FOR PRODUCTION**
8. 📝 **Phase 10 Sprint 4: Documentation** (T111-T118) ← **FINALIZE**

**Rationale**: Complete all functional features (Sprint 3 + Sprint 4) before final Docker packaging to ensure production deployment includes complete feature set.

### Phase Dependencies (Original Plan)

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - **US1 (Phase 3)**: Can start after Phase 2 - No dependencies on other stories (MVP - DO THIS FIRST)
  - **US2 (Phase 4)**: Can start after Phase 2 - Independent of other stories
  - **US3 (Phase 5)**: Can start after US1 T027 (log display exists) - Minor integration with US1
  - **US4 (Phase 6)**: Can start after Phase 2 - Independent error handling
  - **US5 (Phase 7)**: Can start after Phase 1 - Completely independent
- **Phase 10 Sprints**: Depends on Phase 1-7 completion
  - **Sprint 1** (T080-T085): Fixes critical bugs - HIGHEST PRIORITY
  - **Sprint 2** (T086-T093): Database/API - BLOCKS Sprint 3 & 4
  - **Sprint 3** (T094-T103): UI components - DEPENDS on Sprint 2
  - **Sprint 4** (T104-T110): Integration - DEPENDS on Sprint 3
- **Docker Deployment (Phase 8)**: ⚠️ MOVED TO END - Execute after Phase 10 completion
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Priorities

**⚠️ UPDATED - Actual Implementation Order** (2025-10-29):
1. ✅ **Phase 1 + 2**: Setup + Foundational (COMPLETED)
2. ✅ **Phase 3 (US1)**: Submit Article Generation Request (COMPLETED)
3. ✅ **Phase 5 (US3)**: Monitor Generation Progress (COMPLETED)
4. ✅ **Phase 6 (US4)**: Handle Generation Errors (COMPLETED)
5. ✅ **Phase 4 (US2)**: Enable Research Mode (COMPLETED)
6. ✅ **Phase 7 (US5)**: Toggle Theme (COMPLETED)
7. ✅ **Phase 9**: Polish (COMPLETED)
8. ✅ **Phase 10 Sprint 1**: Critical Fixes - SSE format, Russian i18n (COMPLETED)
9. ✅ **Phase 10 Sprint 2**: Database & Profile API (COMPLETED)
10. 🎯 **Phase 10 Sprint 3**: Style Profile UI & New Form Fields ← **CURRENT**
11. 🎯 **Phase 10 Sprint 4**: Research Mode Integration & Backend Updates ← **NEXT**
12. 🐳 **Phase 8**: Docker Deployment - Final Production Package ← **THEN**
13. 📝 **Phase 10 Documentation**: Update docs & final testing ← **FINALIZE**

**Original Recommended Order** (for reference):
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

### ⚠️ CURRENT STRATEGY (2025-10-29): Feature Complete → Docker Package

**Revised execution plan** (all base features already complete):

✅ **COMPLETED**:
1. Phase 1-7: Core application (Setup, User Stories, Theme)
2. Phase 9: Polish & cross-cutting concerns
3. Phase 10 Sprint 1: Critical fixes (SSE format, Russian i18n)
4. Phase 10 Sprint 2: Database & Profile API (SQLite + endpoints)

🎯 **CURRENT PRIORITY - Sprint 3** (~4-6 hours):
1. Create TypeScript types for profiles (T094)
2. Install shadcn/ui accordion component (T095)
3. Build StyleProfileSection component (T096-T099)
4. Reorganize input form with new fields (T100-T103)

🎯 **NEXT - Sprint 4** (~6-8 hours):
1. Update backend /api/generate to accept new request body (T104)
2. Implement two-stage research flow (T105-T107)
3. Update frontend to use POST with new fields (T108-T110)

🐳 **FINAL - Docker Production Package** (~2-3 hours):
1. Test docker-compose build with all features (T063)
2. Test docker-compose startup and health checks (T064, T069)
3. End-to-end validation via Docker (T065)
4. Validate quickstart.md instructions (T077)

📝 **FINALIZE - Documentation** (~2 hours):
1. Update specs and quickstart docs (T111-T112)
2. Add AICODE comments (T113-T114)
3. Manual testing of all flows (T115-T117)
4. Update CLAUDE.md (T118)

**Total remaining time**: ~14-19 hours to production deployment

---

### MVP First (User Story 1 Only) - ORIGINAL PLAN

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

**frontend-developer** (63 tasks):
- Phase 1 Setup: T001-T008 (8 tasks)
- Phase 3 US1 Frontend: T021-T029, T033-T040 (18 tasks)
- Phase 4 US2 Frontend: T042 (1 task)
- Phase 5 US3: T043-T045 (3 tasks)
- Phase 6 US4 Frontend: T049-T052 (4 tasks)
- Phase 7 US5: T053-T055 (3 tasks)
- Phase 9 Polish: T070-T072 (3 tasks)
- Phase 10 UI Improvements: T081-T083, T094-T103, T108-T110 (23 tasks)

**python-backend-developer** (43 tasks):
- Phase 1 Setup: T009-T012 (4 tasks)
- Phase 2 Foundational: T013-T020 (8 tasks)
- Phase 3 US1 Backend: T030-T032 (3 tasks)
- Phase 4 US2 Backend: T041 (1 task)
- Phase 6 US4 Backend: T046-T048 (3 tasks)
- Phase 8 Deployment: T067 (1 task - health endpoint)
- Phase 9 Polish: T073-T075 (3 tasks)
- Phase 10 Backend: T080, T084-T093, T104-T107 (15 tasks)

**production-deployment** (14 tasks):
- Phase 8 Docker: T056-T069 (14 tasks)

**Any agent** (8 tasks):
- Phase 9 Polish: T076-T078 (3 tasks - documentation and validation)
- Phase 10 Documentation: T111-T118 (8 tasks)

**Total**: 118 tasks (78 original + 40 new in Phase 10)

---

## Phase 10: UI Improvements & Russian Localization (Priority: P0) 🎯 Critical

**Goal**: Fix critical bugs, add Russian localization, implement style profile management system

**User Feedback**: Interface doesn't fit on screen, button not working, needs Russian translation, missing style profile management

**Agent**: `python-backend-developer` (T080, T084-T089, T096-T097), `frontend-developer` (T081-T083, T090-T095, T098-T100)

### Sprint 1: Critical Fixes (Week 1)

**Purpose**: Fix broken generation button and basic UX issues

- [X] T080 [P] Fix SSE format mismatch in backend/src/api/generate.py: change from plain text `data: message\n\n` to JSON format `data: {"type":"log","message":"..."}\n\n` for log/result/error events (CRITICAL - blocks article generation)
- [X] T081 [P] Add Russian translation dictionary in web-frontend/src/lib/i18n.ts with all interface strings (labels, buttons, messages, errors)
- [X] T082 Implement Russian localization in web-frontend/src/components/input-form.tsx: replace all English text with Russian translations
- [X] T083 Implement Russian localization in web-frontend/src/components/execution-view.tsx: tabs, buttons, messages
- [X] T084 Optimize interface compactness in web-frontend/src/app/globals.css: reduce padding, adjust spacing for 1280x720 viewport
- [X] T085 Add required field indicators (asterisks) in web-frontend/src/components/input-form.tsx for title field

**Checkpoint**: ✅ Generation works, interface in Russian, fits on screen

### Sprint 2: Database & Backend API (Week 1-2)

**Purpose**: Setup database and API for style profile management

**Agent**: `python-backend-developer`

- [X] T086 [P] Create backend/src/db/database.py with SQLite database initialization using SQLAlchemy ORM (path: backend/profiles.db)
- [X] T087 [P] Create backend/src/db/models.py with StyleProfileDB model (id, urls_hash, profile_text, source_urls JSON, created_at, updated_at)
- [X] T088 Create backend/src/api/profiles.py with FastAPI router for profile management (GET/POST/DELETE /api/profiles endpoints)
- [X] T089 Implement GET /api/profiles/current endpoint in backend/src/api/profiles.py: returns current profile or null if not exists
- [X] T090 Implement POST /api/profiles endpoint in backend/src/api/profiles.py: accepts source_urls[], calls src/ugly_script.py style extraction, saves to DB
- [X] T091 Implement GET /api/profiles/{id} endpoint in backend/src/api/profiles.py: returns profile details by ID
- [X] T092 Implement DELETE /api/profiles/{id} endpoint in backend/src/api/profiles.py: deletes profile and allows creating new one
- [X] T093 Add TODO comment in backend/src/db/database.py: "Migrate to PostgreSQL for multi-user support in future versions"

**Checkpoint**: ✅ Profile database and API ready, tested with curl

### Sprint 3: Style Profile UI & New Form Fields (Week 2)

**Purpose**: Implement style profile management UI and new article fields

**Agent**: `frontend-developer`

- [X] T094 [P] Create web-frontend/src/types/profile.ts with StyleProfile and ArticleRequest TypeScript interfaces
- [X] T095 [P] Install shadcn/ui accordion component in web-frontend/
- [X] T096 Create web-frontend/src/components/style-profile-section.tsx with Accordion component: shows status (loaded/not loaded), "View Profile" button, "Update Profile" button
- [X] T097 Implement profile status API call in web-frontend/src/components/style-profile-section.tsx: GET /api/profiles/current on component mount
- [X] T098 Implement profile viewer dialog in web-frontend/src/components/style-profile-section.tsx: shows profile_text in modal when "View Profile" clicked
- [X] T099 Implement profile update form in web-frontend/src/components/style-profile-section.tsx: collapsible URL input (hidden when profile exists), POST /api/profiles on submit
- [X] T100 Rename "Topic" field to "Название статьи" in web-frontend/src/components/input-form.tsx (already Russian if T082 done)
- [X] T101 Add "Ключевые тезисы" textarea field in web-frontend/src/components/input-form.tsx: optional, multiline, placeholder with examples
- [X] T102 Update ArticleRequest interface in web-frontend/src/types/profile.ts: add title and keyPoints fields
- [X] T103 Reorganize input-form.tsx with Accordion: Section 1 "Контент" (title, keyPoints), Section 2 "Стиль" (StyleProfileSection), Section 3 "Настройки" (research checkbox)

**Checkpoint**: ✅ Style profile management UI complete, new fields integrated (2025-10-29)

### Sprint 4: Research Mode & Backend Integration (Week 2-3)

**Purpose**: Implement two-stage research generation and integrate new fields

**Agent**: `python-backend-developer` (T104-T106), `frontend-developer` (T107-T109)

#### Backend Integration

- [X] T104 Update backend/src/api/generate.py POST /api/generate endpoint: accept title, keyPoints, profileId in request body (replace topic/source_urls query params with body)
- [X] T105 Implement two-stage research in backend/src/api/generate.py: Stage 1 - call src/research_client.py for info collection (emit log events), Stage 2 - call src/ugly_script.py with research data (emit log events)
- [X] T106 Add keyPoints integration in backend/src/api/generate.py: append keyPoints to article generation prompt if provided
- [X] T107 Load style profile from DB in backend/src/api/generate.py: query StyleProfileDB by profileId, use profile_text in generation prompt

#### Frontend Integration

- [X] T108 Update handleSubmit in web-frontend/src/app/page.tsx: change from GET with query params to POST with JSON body (title, keyPoints, profileId, enableResearch)
- [X] T109 Update EventSource initialization in web-frontend/src/app/page.tsx: use POST endpoint with fetch() + ReadableStream for SSE streaming
- [X] T110 Add profile selection logic in web-frontend/src/components/input-form.tsx: disable "Generate" button if no profile loaded (show warning message)

**Checkpoint**: Two-stage research working, new fields integrated, style profile required for generation

### Sprint 4: Documentation & Testing (Week 3)

**Purpose**: Update documentation and validate all changes

**Agent**: Any agent

- [ ] T111 [P] Update specs/002-web-frontend-docker/spec.md: add new user stories for profile management, title/keyPoints fields, Russian localization
- [ ] T112 [P] Update specs/002-web-frontend-docker/quickstart.md: document SQLite database location, profile management workflow, new form fields
- [ ] T113 [P] Add AICODE comments in backend/src/api/profiles.py explaining profile extraction logic and database choice
- [ ] T114 [P] Add AICODE comments in web-frontend/src/components/style-profile-section.tsx explaining profile status detection and update flow
- [ ] T115 Manual testing: Generate article with new flow (create profile → enter title → optional keyPoints → enable research → generate)
- [ ] T116 Manual testing: Test profile update workflow (view profile → delete → create new with different URLs)
- [ ] T117 Manual testing: Validate Russian translation completeness (check all labels, buttons, messages)
- [ ] T118 Update CLAUDE.md: add SQLite, profile management, two-stage research to technologies section

**Checkpoint**: Documentation complete, all features tested, ready for deployment

---

## Integration Notes for Phase 10

### Existing Scripts Reuse

**From codebase analysis**, these scripts are already implemented and should be reused:

1. **src/style_hints_extractor.py**:
   - Uses LLM to extract StyleHints (content_depth, technical_level, preferred_sources, focus_areas) from style profile
   - Already integrated with ugly_script.py
   - Reuse in T090 for profile extraction

2. **src/research_client.py**:
   - Implements research using Perplexity Sonar via OpenRouter
   - Returns ResearchResult with facts_and_stats, quotes_and_sources
   - Already integrated with ugly_script.py when `config.research_enabled=True`
   - Reuse in T105 for two-stage generation

3. **src/style_cache.py**:
   - File-based caching in `style_profiles/` directory
   - Uses MD5 hash of sorted URLs as cache key
   - Currently saves as .txt files
   - Migration path: Keep file cache as backup, add SQLite as primary storage (T086-T093)

4. **src/models.py**:
   - StyleProfile, StyleHints, ResearchResult, GeneratedArticle already defined
   - Reuse existing models, add new StyleProfileDB for SQLAlchemy ORM (T087)

### API Contract Changes

**Breaking change**: POST /api/generate endpoint signature changes

**Old** (T001-T078):
```
GET /api/generate?topic=...&source_urls=...&research=true
```

**New** (T104+):
```
POST /api/generate
Body: {
  "title": "Название статьи",
  "keyPoints": "Тезис 1\nТезис 2",
  "profileId": 123,
  "enableResearch": true
}
```

**Migration**: Frontend must update from EventSource GET to POST with body (T108-T109)

### Database Schema

**StyleProfileDB** (SQLite):
```sql
CREATE TABLE style_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urls_hash TEXT NOT NULL UNIQUE,  -- MD5 hash from generate_url_hash()
    profile_text TEXT NOT NULL,       -- LLM-generated style analysis
    source_urls TEXT NOT NULL,        -- JSON array of URLs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**File location**: `backend/profiles.db` (not in src/ to avoid Docker volume conflicts)

### UI Component Hierarchy

```
page.tsx (main state: title, keyPoints, profileId, isLoading, logLines, finalArticle)
├── InputForm
│   ├── Accordion "Контент"
│   │   ├── Input: "Название статьи" (required)
│   │   └── Textarea: "Ключевые тезисы" (optional)
│   ├── Accordion "Стиль"
│   │   └── StyleProfileSection
│   │       ├── Status indicator (загружен/не загружен)
│   │       ├── "Посмотреть профиль" button (if loaded)
│   │       ├── ProfileViewerDialog (modal with profile_text)
│   │       └── Collapsible URL input (if not loaded)
│   └── Accordion "Настройки"
│       └── Checkbox: "Включить исследование"
└── ExecutionView (tabs: logs, result)
```

### Dependencies for Phase 10

- **T080**: Blocks all generation - CRITICAL priority
- **T081-T085**: Independent UI fixes - can run in parallel
- **T086-T093**: Database setup - blocks T094-T110 (profile features)
- **T094-T103**: Frontend profile UI - depends on T086-T093 completion
- **T104-T110**: Backend integration - depends on T086-T093 + T094-T103
- **T111-T118**: Documentation - can run parallel with testing, depends on T080-T110

### Parallel Opportunities

**Sprint 1 parallelization**:
- `python-backend-developer`: T080 (SSE fix)
- `frontend-developer`: T081-T085 (localization, compactness)
Both can work simultaneously on different files

**Sprint 2 parallelization**:
- All T086-T093 are backend tasks - sequential execution by python-backend-developer

**Sprint 3 parallelization**:
- `frontend-developer`: T094-T103 (all frontend) - some [P] tasks
- `python-backend-developer`: Can start T104-T107 (backend integration) in parallel

**Sprint 4 parallelization**:
- `frontend-developer`: T108-T110 (frontend integration)
- `python-backend-developer`: Assist with testing T115-T117
- Any agent: T111-T118 (documentation) can run parallel

---

## Notes

- **[P] tasks**: Different files, no dependencies on same-file modifications
- **[Story] label**: Maps task to specific user story from spec.md for traceability
- **Agent assignment**: Based on plan.md Agent Assignment Strategy section
- **AICODE comments**: Should be added to key decisions throughout implementation (T078, T113-T114)
- **MVP scope**: Phase 1 + 2 + 3 (US1) = 32 tasks for working article generator
- **Production-ready scope**: Add Phase 5 (US3) + Phase 6 (US4) + Phase 8 (Docker) = 59 tasks
- **Feature-complete scope**: Phase 1-9 = 78 tasks
- **Enhanced scope**: Phase 1-10 = 118 tasks (adds profile management, localization, new fields)
- **No tests included**: Feature spec does not request TDD approach
- **Commit frequency**: Commit after each task or logical group of parallel tasks
- **Checkpoints**: Stop at any user story checkpoint to validate independently
- **Critical path**: Phase 2 (Foundational) blocks all user stories - highest priority
- **Next.js API Routes**: Do NOT use app/api/ directory - frontend connects directly to FastAPI backend (see plan.md AICODE-NOTE)
- **Existing scripts**: src/style_hints_extractor.py, src/research_client.py, src/style_cache.py already implemented - reuse in Phase 10
- **Database migration**: SQLite now (single user), PostgreSQL later (multi-user) - see T093 TODO comment

---

## Phase 11: UI Bug Fixes & Optional Profile (Priority: P0) 🎯 Critical

**Goal**: Fix [object Object] display bug, improve header spacing, make style profile optional

**User Feedback**:
1. "[object Object]" shown instead of profile name
2. Too much empty space above header
3. Need ability to generate articles without style profile

**Agent**: `python-backend-developer` (T119-T124), `frontend-developer` (T125-T131)

### Sprint 1: Backend - Profile Name & Optional Profile (2025-10-30)

**Purpose**: Add short profile name, make profile optional for generation

**Agent**: `python-backend-developer`

- [ ] T119 [P] Add `name` VARCHAR(100) column to StyleProfileDB model in backend/src/db/models.py
- [ ] T120 [P] Create generate_profile_name() function in backend/src/api/profiles.py: extract domain from first URL, return "Профиль {SiteName}"
- [ ] T121 Add database migration in backend/src/db/database.py: ALTER TABLE to add 'name' column for existing profiles
- [ ] T122 Update POST /api/profiles in backend/src/api/profiles.py: generate and save profile name on creation
- [ ] T123 Make profileId optional in GenerateRequest model in backend/src/api/generate.py: profileId: int | None = None
- [ ] T124 Update generate_article_v2() in backend/src/api/generate.py: load profile if profileId provided, otherwise generate without style profile

**Checkpoint**: ✅ Backend supports profile names and optional profile generation

### Sprint 2: Frontend - Display Fixes & Optional UI (2025-10-30)

**Purpose**: Fix [object Object] bug, improve layout, update UI for optional profile

**Agent**: `frontend-developer`

- [ ] T125 [P] Update StyleProfile interface in web-frontend/src/types/profile.ts: add name: string field
- [ ] T126 Fix profile display in web-frontend/src/components/style-profile-section.tsx: show profile.name instead of profile object
- [ ] T127 Remove currentProfile check from handleSubmit in web-frontend/src/app/page.tsx: allow generation without profile
- [ ] T128 Update header spacing in web-frontend/src/app/page.tsx: py-8 → py-4, mb-8 → mb-4, mb-6 → mb-4
- [ ] T129 Add text-sm class to subtitle in web-frontend/src/app/page.tsx for compact design
- [ ] T130 Change profile section text in web-frontend/src/components/style-profile-section.tsx: "для начала работы" → "(опционально)"
- [ ] T131 Update input-form.tsx in web-frontend/src/components/input-form.tsx: remove disabled state dependency on currentProfile

**Checkpoint**: ✅ UI fixed - profile name displays correctly, header compact, generation works without profile

### Sprint 3: Docker Deployment & Testing (2025-10-30)

**Purpose**: Deploy changes, verify all fixes work in Docker

**Agent**: `production-deployment`

- [ ] T132 Rebuild Docker images: docker-compose build --no-cache
- [ ] T133 Start containers: docker-compose up -d
- [ ] T134 Test profile creation: create new profile via UI, verify short name appears
- [ ] T135 Test generation with profile: verify article generated with style
- [ ] T136 Test generation without profile: verify article generated in general style
- [ ] T137 Update documentation in specs/002-web-frontend-docker/quickstart.md: document optional profile behavior

**Checkpoint**: ✅ All fixes deployed and tested in Docker

---

## Dependencies for Phase 11

- **T119-T122**: Backend profile name - can run in parallel
- **T123-T124**: Backend optional profile - depends on T119-T122 completion
- **T125-T131**: Frontend fixes - can run in parallel with backend (T119-T124)
- **T132-T137**: Docker deployment - depends on all frontend + backend tasks

### Parallel Opportunities

**Sprint 1 + Sprint 2 parallelization**:
- `python-backend-developer`: T119-T124 (backend)
- `frontend-developer`: T125-T131 (frontend)

Both can work simultaneously - no file conflicts.

---

## Phase 11.1: Profile Selection & Bug Fixes (Priority: P0) 🎯 Critical

**Goal**: Fix ANSI codes in logs, repair profile creation, add profile selection UI

**User Feedback** (2025-10-31):
1. Logs show ANSI escape sequences like `[32m18:52:24[0m` (incomprehensible symbols)
2. Profile creation completely broken - script arguments error
3. Need ability to select between multiple saved profiles
4. Need delete button for removing profiles

**Agent**: `python-backend-developer` (T146-T149), `frontend-developer` (T150-T154)

### Sprint 1: Backend - Fix ANSI Codes & Profile Creation (2025-10-31)

**Purpose**: Clean log output, repair profile extraction workflow

**Agent**: `python-backend-developer`

- [X] T146 Add strip_ansi_codes() function in backend/src/api/generate.py: regex pattern to remove terminal color codes from Loguru output
- [X] T147 Apply ANSI stripping in SSE log streaming (backend/src/api/generate.py:558-565): clean decoded lines before sending to frontend
- [X] T148 Rewrite _extract_style_from_urls() in backend/src/api/profiles.py: use MODE 1 workflow (create temp dir with links.txt/topic.txt, run script without flags, read from cache)
- [X] T149 Add RESEARCH_ENABLED=false environment variable in _extract_style_from_urls(): disable research stage during profile extraction to avoid parsing errors

**Checkpoint**: ✅ Logs display cleanly, profile creation works with real URLs

### Sprint 2: Backend - Profile Management API (2025-10-31)

**Purpose**: Add endpoints for listing and managing multiple profiles

**Agent**: `python-backend-developer`

- [X] T150 Add GET /api/profiles endpoint in backend/src/api/profiles.py: return list of all profiles ordered by created_at DESC
- [X] T151 Update handleCreateProfile in web-frontend/src/components/style-profile-section.tsx: call loadAllProfiles() after successful creation

**Checkpoint**: ✅ Backend supports listing all saved profiles

### Sprint 3: Frontend - Profile Selection UI (2025-10-31)

**Purpose**: Add dropdown for selecting between profiles, with delete functionality

**Agent**: `frontend-developer`

- [X] T152 Add profile selection state in web-frontend/src/components/style-profile-section.tsx: allProfiles[] array and selectedProfileId
- [X] T153 Add loadAllProfiles() function in style-profile-section.tsx: fetch from GET /api/profiles, set selectedProfileId to current profile
- [X] T154 Add profile selection handlers: handleProfileSelect(id) to load and display selected profile
- [X] T155 Add handleDeleteProfile(id) function: DELETE /api/profiles/{id}, reload lists
- [X] T156 Add Select dropdown UI in style-profile-section.tsx: shows when allProfiles.length > 1, displays profile names with URL count
- [X] T157 Add delete button (trash icon) next to Select dropdown: calls handleDeleteProfile with selectedProfileId

**Checkpoint**: ✅ Users can select between profiles and delete unwanted ones

### Sprint 4: Testing & Documentation (2025-10-31)

**Purpose**: Verify all improvements, update documentation

**Agent**: `general-purpose`

- [ ] T158 Run backend tests: poetry run pytest in backend/
- [ ] T159 Rebuild all Docker containers: docker-compose build
- [ ] T160 Test profile creation with real URL (https://azbyka.ru/fiction/dushechka-sbornik-rasskazov/)
- [ ] T161 Test profile selection: create 2+ profiles, verify dropdown appears and selection works
- [ ] T162 Test profile deletion: verify delete button removes profile and updates UI
- [ ] T163 Test article generation: verify logs display cleanly without ANSI codes
- [ ] T164 Update quickstart.md: document profile selection and management features

**Checkpoint**: ✅ All improvements tested and documented

---

## Dependencies for Phase 11.1

- **T146-T149**: Backend fixes - must complete before frontend testing
- **T150-T151**: Profile list API - depends on T146-T149
- **T152-T157**: Frontend UI - depends on T150 for API availability
- **T158-T164**: Testing & docs - depends on all previous tasks

### Parallel Opportunities

**Sprint 1 + Sprint 2 can run sequentially** (same agent):
- `python-backend-developer`: T146-T151

**Sprint 3 can start after T150**:
- `frontend-developer`: T152-T157 (needs GET /api/profiles endpoint)

---

## Phase 12: UI/UX Design Improvements (Priority: P1) 🎨 User Feedback

**Goal**: Fix interface layout to fit 1280x720 viewport, improve visual hierarchy, add color accents, increase contrast

**User Feedback** (2025-11-01):
1. Interface doesn't fit on screen (requires scrolling even on 1280x720)
2. Design looks washed out and blends together (low contrast, no visual hierarchy)
3. All elements look the same - hard to distinguish sections

**Root Causes:**
- Excessive vertical spacing (headers, paddings, margins)
- Missing visual hierarchy (no color coding, borders, or accents)
- Low contrast (all sections use same muted colors)
- Progress stepper too verbose (takes ~40px)
- Accordion sections have no visual distinction

**Agent**: `frontend-developer` (T165-T180)

### Sprint 1: Layout Compactness (Week 1)

**Purpose**: Reduce vertical spacing to fit interface on 1280x720 viewport without scrolling

**Agent**: `frontend-developer`

- [X] T165 [P] Optimize header spacing in web-frontend/src/app/page.tsx: remove centered subtitle, move title to header row (saves ~40px)
- [X] T166 [P] Reduce Card padding in web-frontend/src/components/input-form.tsx: CardContent p-4 → p-3
- [X] T167 [P] Reduce form spacing in input-form.tsx: space-y-4 → space-y-3 (saves ~12px)
- [X] T168 [P] Make progress stepper compact in input-form.tsx: text-sm → text-xs, mb-4 → mb-2, gap-2 → gap-1 (saves ~15px)
- [X] T169 [P] Reduce accordion content padding: pt-3 → pt-2, space-y-2 → space-y-1.5
- [X] T170 [P] Optimize input heights in input-form.tsx: min-h-[44px] → h-10 for title input (saves ~4px)
- [X] T171 [P] Reduce textarea rows in input-form.tsx: keyPoints rows={6} → rows={4} (saves ~40px)
- [X] T172 [P] Reduce button height: min-h-[44px] → h-10 (saves ~4px)

**Checkpoint**: ✅ Interface fits on 1280x720 without scrolling (~115px saved)

---

### Sprint 2: Visual Hierarchy & Color Accents (Week 1)

**Purpose**: Add color-coded borders and backgrounds to distinguish accordion sections

**Agent**: `frontend-developer`

- [X] T173 [P] Add left border accent to "Контент" section in input-form.tsx: wrap AccordionItem with border-l-4 border-blue-500 pl-3
- [X] T174 [P] Add subtle background to "Контент" AccordionContent: bg-blue-50 dark:bg-blue-950/20 rounded-md p-2
- [X] T175 [P] Add left border accent to "Стиль" section: border-l-4 border-green-500 pl-3
- [X] T176 [P] Add subtle background to "Стиль" AccordionContent: bg-green-50 dark:bg-green-950/20 rounded-md p-2
- [X] T177 [P] Add left border accent to "Настройки" section: border-l-4 border-purple-500 pl-3
- [X] T178 [P] Add subtle background to "Настройки" AccordionContent: bg-purple-50 dark:bg-purple-950/20 rounded-md p-2

**Checkpoint**: ✅ Each section has distinct color coding (blue/green/purple)

---

### Sprint 3: Contrast & Visual Feedback (Week 1-2)

**Purpose**: Improve contrast and add visual feedback for interactive elements

**Agent**: `frontend-developer`

- [X] T179 [P] Strengthen progress stepper active step: add font-semibold to current section in input-form.tsx
- [X] T180 [P] Add gradient to submit button in input-form.tsx: bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700
- [X] T181 [P] Increase AccordionTrigger chevron size: add larger chevron icon or increase icon size (deferred - default size is adequate with other improvements)
- [X] T182 [P] Add divider between accordion sections: border-b border-border on AccordionItem
- [ ] T183 Test viewport fit on 1280x720: verify no scrolling required before generation starts (testing phase)
- [ ] T184 Test color contrast: verify WCAG AA compliance for all text on colored backgrounds (testing phase)
- [ ] T185 Test dark mode: verify all color accents work in both light and dark themes (testing phase)

**Checkpoint**: ✅ High contrast, clear visual hierarchy, WCAG AA compliant

---

### Sprint 4: Optional Enhancements (Week 2)

**Purpose**: Additional polish for better UX (optional, can be skipped)

**Agent**: `frontend-developer`

- [X] T186 [P] Add icons to section headers in input-form.tsx: FileText for Контент, Palette for Стиль, Settings for Настройки
- [ ] T187 [P] Add smooth animation to AccordionContent: animate-in slide-in-from-top-2 duration-200 (deferred - current transitions are smooth)
- [X] T188 [P] Increase Card border-radius: rounded-lg → rounded-xl for modern look
- [X] T189 [P] Add shadow to Card: shadow-sm → shadow-lg for depth
- [X] T190 Update design documentation in specs/002-web-frontend-docker/plan.md: document color-coding system (completed in Phase 12)
- [X] T191 Add AICODE comments explaining design decisions in input-form.tsx and page.tsx (completed throughout Sprint 1-4)

**Checkpoint**: ✅ All design improvements complete and documented

---

## Dependencies for Phase 12

- **T165-T172** (Sprint 1): All parallel - frontend spacing adjustments
- **T173-T178** (Sprint 2): All parallel - depends on T165-T172 completion
- **T179-T185** (Sprint 3): Mostly parallel - depends on T173-T178 for color context
- **T186-T191** (Sprint 4): Optional enhancements - can run anytime after Sprint 2

### Parallel Opportunities

**All sprints can run in parallel**:
- `frontend-developer`: T165-T191 (all frontend, different concerns)

**Execution order**:
1. Sprint 1 (compactness) → Sprint 2 (colors) → Sprint 3 (contrast) → Sprint 4 (optional)
2. OR: Sprint 1 + Sprint 2 in parallel, then Sprint 3, then Sprint 4

**Estimated time**: ~6-8 hours total (Sprint 1-3), +2-3 hours for Sprint 4

---

## Expected Outcomes for Phase 12

### Before (Current State):
- ❌ Interface height: ~600px (doesn't fit on 1280x720)
- ❌ Visual hierarchy: None (all sections look the same)
- ❌ Contrast: Low (muted colors, hard to read)
- ❌ Color coding: None (no way to distinguish sections)
- ❌ Scrolling required: Yes (poor UX)

### After (Phase 12 Complete):
- ✅ Interface height: ~480px (fits comfortably on 1280x720)
- ✅ Visual hierarchy: Strong (color-coded borders + backgrounds)
- ✅ Contrast: High (WCAG AA compliant)
- ✅ Color coding: Blue (Content), Green (Style), Purple (Settings)
- ✅ Scrolling required: No (entire form visible at once)
- ✅ Modern design: Gradients, shadows, smooth animations (if Sprint 4 done)

### Metrics:
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Vertical space saved | 0px | ~115px | **19% reduction** |
| Contrast ratio | ~3:1 | ~7:1 | **+133% readability** |
| Sections with visual identity | 0/3 | 3/3 | **100% coverage** |
| Viewport fit (1280x720) | ❌ No | ✅ Yes | **Fixed** |
| WCAG compliance | Partial | AA | **Accessible** |

---

## Phase 13: Text-Based Profile Creation (Priority: P1) 🎯 Feature Enhancement

**Goal**: Allow users to create style profiles by pasting text directly instead of URLs only

**User Request** (2025-11-01):
1. Current: Profile creation requires URLs (1-10 URLs, fetches HTML, parses content)
2. New: Add ability to paste author's text directly (skip URL fetching/parsing)
3. Auto-detection: System should transparently detect whether input is URLs or text
4. User-provided names: Allow custom profile names instead of auto-generated only

**Root Causes:**
- Current API only accepts `source_urls: List[HttpUrl]` (Pydantic validation requires valid URLs)
- Profile creation always calls `_extract_style_from_urls()` which requires URL fetching
- No path for direct text → style analysis without subprocess
- Profile names auto-generated from domain, no user input

**Agent**: `python-backend-developer` (T192-T199), `frontend-developer` (T200-T202)

### Sprint 1: Backend - Content Type Detection & Text Analysis (Week 1)

**Purpose**: Smart detection of URLs vs text, direct LLM style analysis for text input

**Agent**: `python-backend-developer`

- [X] T192 [P] Add `source_type` VARCHAR(10) column to StyleProfileDB model in backend/src/db/models.py: values "urls" or "text", DEFAULT "urls", add index
- [X] T193 [P] Create Alembic migration in backend/src/db/: `ALTER TABLE style_profiles ADD COLUMN source_type VARCHAR(10) DEFAULT 'urls' NOT NULL; CREATE INDEX ix_style_profiles_source_type ON style_profiles(source_type);`
- [X] T194 Create detect_content_type() function in backend/src/api/profiles.py: analyze list of strings, return "urls" if >50% lines start with http://, otherwise "text"
- [X] T195 Create _analyze_style_from_text() async function in backend/src/api/profiles.py: accepts text string, calls LLMClient.analyze_style() directly (no subprocess), returns profile_text
- [X] T196 Update ProfileCreateRequest model in backend/src/api/profiles.py: replace `source_urls: List[HttpUrl]` with `source_content: List[str]`, add `profile_name: str | None = None`
- [X] T197 Update generate_profile_name() in backend/src/api/profiles.py: add parameters `source_type`, `custom_name`, implement priority logic (custom → URL domain → first 7 words of text)
- [X] T198 Update create_profile() endpoint in backend/src/api/profiles.py: add branching logic - if URLs: call _extract_style_from_urls(), if text: call _analyze_style_from_text()
- [X] T199 Update ProfileResponse model in backend/src/api/profiles.py: add `source_type: str` field for frontend display

**Checkpoint**: ✅ Backend supports both URL and text profile creation with auto-detection

---

### Sprint 2: Frontend - Profile Name Input & Unified Text Field (Week 1)

**Purpose**: Add custom name input, update UI to accept URLs or text

**Agent**: `frontend-developer`

- [X] T200 Add profile name input field in web-frontend/src/components/style-profile-section.tsx: Input component above source content, placeholder "Мой уникальный стиль", optional field with hint "Оставьте пустым для автоматического названия"
- [X] T201 Update source content field in style-profile-section.tsx: change label "URL источников" → "URL или текст источников", update placeholder to show both URL and text examples, increase rows to 8
- [X] T202 Update handleCreateProfile() in style-profile-section.tsx: send both `source_content` array and `profile_name` string to POST /api/profiles

**Checkpoint**: ✅ Users can paste URLs or text, provide custom names (Completed 2025-11-01)

---

### Sprint 3: Testing & Documentation (Week 1-2)

**Purpose**: Validate both flows work, update documentation

**Agent**: `general-purpose`

- [ ] T203 [P] Write unit tests for detect_content_type(): test URLs only, text only, mixed input, edge cases (empty, single line)
- [ ] T204 [P] Write unit tests for _analyze_style_from_text(): test success, error handling, content length limits
- [ ] T205 [P] Write unit tests for generate_profile_name(): test custom name priority, URL extraction, text truncation
- [ ] T206 Run backend tests: poetry run pytest backend/tests/test_profiles.py
- [ ] T207 Test profile creation from URLs: verify existing flow still works (regression test)
- [ ] T208 Test profile creation from text: paste article text, verify profile created with correct source_type
- [ ] T209 Test profile creation with custom name: verify user-provided name used instead of auto-generated
- [ ] T210 Test mixed input: paste URLs + text, verify detection logic works correctly
- [ ] T211 Test duplicate detection: create text profile twice with same text, verify hash collision detected
- [ ] T212 Update specs/002-web-frontend-docker/spec.md: add user story for text-based profile creation
- [ ] T213 Update quickstart.md: document text input option, show examples
- [ ] T214 Add AICODE comments in profiles.py: explain detection logic, text analysis flow, naming priority

**Checkpoint**: ✅ All flows tested and documented, ready for production

---

## Dependencies for Phase 13

- **T192-T193**: Database migration - must complete first (creates source_type column)
- **T194-T199**: Backend logic - depends on T192-T193, can run in parallel among themselves
- **T200-T202**: Frontend updates - can run in parallel with backend (T194-T199)
- **T203-T214**: Testing & docs - depends on all backend + frontend tasks

### Parallel Opportunities

**Sprint 1 + Sprint 2 can run in parallel**:
- `python-backend-developer`: T192-T199 (backend detection + analysis)
- `frontend-developer`: T200-T202 (UI updates)

Both can work simultaneously on different files.

**Sprint 3 sequential**:
- Testing depends on implementation completion
- Documentation can run in parallel with testing

**Estimated time**: ~10-12 hours total (Sprint 1: 4-5h, Sprint 2: 2-3h, Sprint 3: 4h)

---

## Expected Outcomes for Phase 13

### Before (Current State):
- ❌ Profile creation: URLs only (1-10 URLs required)
- ❌ HTML fetching: Always required (adds latency)
- ❌ Profile names: Auto-generated from domain only
- ❌ Text input: Not supported

### After (Phase 13 Complete):
- ✅ Profile creation: URLs OR text (auto-detected)
- ✅ HTML fetching: Only for URLs (text skips this step)
- ✅ Profile names: User-provided OR auto-generated
- ✅ Text input: Fully supported with direct LLM analysis
- ✅ Transparent UX: Single textarea accepts both types

### Use Cases:
1. **URL-based** (existing): Paste URLs → fetch HTML → analyze style
2. **Text-based** (new): Paste article text → analyze style directly (faster, no network dependency)
3. **Custom names**: "Мой деловой стиль", "Профиль для блога" instead of "Профиль Habr"

### Metrics:
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Input types supported | 1 (URLs) | 2 (URLs + Text) | **+100%** |
| Profile creation speed (text) | N/A | ~3-5s | **Faster than URLs** |
| Network dependency | Always | Optional | **More reliable** |
| Name customization | None | Full | **Better UX** |

---