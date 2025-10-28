# Implementation Plan: Web Frontend with Docker Deployment

**Branch**: `002-web-frontend-docker` | **Date**: 2025-10-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-web-frontend-docker/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a production-ready web interface for the existing Python article generation script. The system provides real-time streaming feedback using Server-Sent Events (SSE), graceful error handling, and Docker deployment. Frontend uses Next.js with shadcn/ui components and Tailwind CSS following Linear/Vercel design philosophy (dark zinc theme, minimal noise). Backend is FastAPI serving as an SSE gateway to the existing Python script, with robust process management to prevent resource leaks.

**Key Technical Decisions**:
- Next.js 14 App Router for frontend (SSR + client streaming)
- shadcn/ui + Tailwind for consistent, accessible UI components
- FastAPI for streaming API backend (SSE support)
- Docker Compose for multi-service deployment
- Process lifecycle management to prevent zombie processes

## Technical Context

**Language/Version**:
- Frontend: TypeScript 5.x, Next.js 14.x
- Backend: Python 3.11+

**Primary Dependencies**:
- Frontend: React 18, shadcn/ui, Tailwind CSS 3.x, lucide-react (icons)
- Backend: FastAPI 0.100+, uvicorn, asyncio (subprocess management)
- Existing: poetry (Python dependency management)

**Storage**:
- Temporary files for script I/O (topic.txt, output.txt)
- Browser localStorage for theme preference
- No persistent database required

**Testing**:
- Frontend: Jest + React Testing Library (unit), Playwright (E2E)
- Backend: pytest + pytest-asyncio (async tests), httpx (SSE client tests)

**Target Platform**:
- Development: macOS/Linux
- Production: Linux server (Docker containers)

**Project Type**: Web application (frontend + backend)

**Performance Goals**:
- SSE message latency: < 500ms (SC-002)
- First log message: < 2 seconds (SC-001)
- Theme toggle: < 200ms (SC-009)
- Container startup: < 30 seconds (SC-010)

**Constraints**:
- Real-time streaming required (no polling)
- Must handle articles up to 50K characters (SC-008)
- Process cleanup within 5 seconds of disconnect (SC-012)
- Graceful degradation when URLs fail (SC-011)

**Scale/Scope**:
- Single-user sessions (no multi-tenancy in v1)
- Expected load: < 10 concurrent generations
- Article size: up to 50,000 characters
- Log volume: ~100-500 lines per generation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: No project constitution defined yet - skipping gates.

This is a new web frontend addition to an existing Python script. When constitution is established, verify:
- Separation of concerns (frontend/backend boundaries)
- Testing requirements (unit, integration, E2E coverage)
- Deployment and versioning strategy
- Performance and observability standards

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
web-frontend/                    # NEW: Next.js frontend (CLIENT ONLY - NO API ROUTES)
├── src/
│   ├── app/                     # Next.js 14 App Router
│   │   ├── page.tsx             # Main page with generation UI
│   │   ├── layout.tsx           # Root layout with theme provider
│   │   └── globals.css          # Tailwind imports
│   ├── components/              # React components
│   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── checkbox.tsx
│   │   │   ├── tabs.tsx
│   │   │   └── alert.tsx
│   │   ├── theme-toggle.tsx     # Theme switcher component
│   │   ├── input-form.tsx       # Input card component
│   │   └── execution-view.tsx   # Tabs with log/result
│   └── lib/
│       └── utils.ts             # cn() helper, etc.
├── public/                      # Static assets
├── tests/
│   ├── unit/                    # Component tests
│   └── e2e/                     # Playwright tests
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── components.json              # shadcn/ui config
├── next.config.js
└── .env.local                   # NEXT_PUBLIC_API_URL=http://backend:8000

# AICODE-NOTE: NO Next.js API routes (app/api/) - frontend is pure client
# EventSource connects directly to FastAPI backend for SSE streaming
# Next.js API Routes are serverless with 10-60s timeout limits
# SSE + subprocess management require long-running server (FastAPI in Docker)

backend/                         # NEW: FastAPI backend
├── src/
│   ├── main.py                  # FastAPI app entry
│   ├── api/
│   │   └── generate.py          # SSE streaming endpoint
│   └── services/
│       └── process_manager.py   # Subprocess lifecycle management
├── tests/
│   ├── test_streaming.py        # SSE tests
│   └── test_process_mgmt.py     # Zombie prevention tests
├── pyproject.toml               # Add FastAPI dependencies
└── Dockerfile

src/                             # EXISTING: Python article script
├── ugly_script.py               # (or whatever current name)
└── ...

docker-compose.yml               # NEW: Multi-service orchestration
.dockerignore                    # NEW: Docker ignore patterns
```

**Structure Decision**:

Web application structure (Option 2) chosen. Two new top-level directories:

1. **web-frontend/**: Next.js 14 app with App Router, TypeScript, and shadcn/ui components. Self-contained with own package.json and test suite.

2. **backend/**: FastAPI service that wraps the existing Python script (in `src/`) with SSE streaming. Manages subprocess lifecycle to prevent zombies.

3. **src/**: Existing Python article generator - minimal changes. Backend invokes it via subprocess.

Docker Compose orchestrates frontend (port 3000), backend (port 8000), with shared network. Production uses multi-stage builds for optimization.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution defined yet. When established, this feature adds:
- Two new project directories (web-frontend, backend)
- New technology stacks (TypeScript/React, FastAPI)
- Docker orchestration layer

These additions are justified by the core requirement (web UI for existing script) and cannot be simplified without losing real-time streaming capability or production deployment support.

---

## Agent Assignment Strategy

**Available Agents:**
- **frontend-developer** - Next.js 14+, React, TypeScript, shadcn/ui, Tailwind CSS
- **python-backend-developer** - FastAPI, Python 3.11+, asyncio, pytest, TDD
- **production-deployment** - Docker, docker-compose, Linux server deployment

### Task-to-Agent Mapping

| Functional Requirements | Assigned Agent | Rationale |
|------------------------|----------------|-----------|
| FR-001 to FR-015 | `frontend-developer` | All UI components, client-side streaming, theme management |
| FR-016 to FR-021 | `python-backend-developer` | SSE backend, subprocess management, process lifecycle |
| FR-022 to FR-023 | `production-deployment` | Docker containerization and deployment |

### Component-Level Assignment

**Frontend (frontend-developer):**
```
web-frontend/
├── components/
│   ├── input-form.tsx          # FR-002, FR-003, FR-003.1, FR-003.2, FR-004.1
│   ├── execution-view.tsx      # FR-005, FR-006, FR-007, FR-008, FR-009
│   ├── theme-toggle.tsx        # FR-014, FR-015
│   └── ui/                     # FR-024 (shadcn/ui components)
└── app/
    └── page.tsx                # FR-001, FR-025 (main integration)
```

**Backend (python-backend-developer):**
```
backend/
├── src/
│   ├── main.py                 # FastAPI app setup
│   ├── api/
│   │   └── generate.py         # FR-016, FR-018, FR-019, FR-020, FR-021
│   └── services/
│       └── process_manager.py  # FR-016.1, FR-016.2, FR-017, FR-017.1, FR-018.1
└── tests/
    ├── test_streaming.py       # SSE integration tests
    └── test_process_mgmt.py    # Zombie prevention tests
```

**Deployment (production-deployment):**
```
./
├── docker-compose.yml          # FR-022 (multi-service orchestration)
├── backend/Dockerfile          # FR-022 (backend container)
├── web-frontend/Dockerfile     # FR-022 (frontend container)
└── .dockerignore               # FR-022 (optimization)
```

### Execution Strategy

**Phase 1: Backend Foundation** (python-backend-developer)
```
Sequential execution required:
1. Setup FastAPI project structure
2. Implement ProcessManager service (FR-016.1, FR-016.2)
3. Implement SSE streaming endpoint (FR-016 to FR-021)
4. Add graceful URL failure handling (FR-017.1, FR-018.1)
5. Write tests (pytest + httpx for SSE)

Estimated: 8-12 hours
Critical path: Yes (frontend depends on this)
```

**Phase 2: Frontend Development** (frontend-developer)
```
Can start in parallel with Phase 1 using mock API:
1. Setup Next.js project + shadcn/ui
2. Implement InputForm component (FR-002, FR-003)
3. Implement ExecutionView component (FR-005 to FR-009)
4. Implement ThemeToggle component (FR-014, FR-015)
5. Integrate with real backend API
6. Write tests (Jest + Playwright)

Estimated: 6-10 hours
Can start: After Phase 1 Step 3 (API contract ready)
```

**Phase 3: Docker Deployment** (production-deployment)
```
Sequential execution (depends on Phase 1 + 2):
1. Create Dockerfiles (multi-stage builds)
2. Create docker-compose.yml
3. Test local deployment
4. Deploy to production server
5. Verify health checks

Estimated: 3-5 hours
Can start: After Phase 1 + 2 complete
```

### Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Backend (python-backend-developer)                     │
│ ┌─────────────┐    ┌──────────────┐    ┌──────────────┐       │
│ │  Setup      │───▶│ProcessManager│───▶│SSE Streaming │       │
│ │  FastAPI    │    │  Service     │    │  Endpoint    │       │
│ └─────────────┘    └──────────────┘    └──────┬───────┘       │
└────────────────────────────────────────────────┼───────────────┘
                                                  │
                                   ┌──────────────▼──────────────┐
                                   │ API Contract Published       │
                                   └──────────────┬──────────────┘
                                                  │
┌─────────────────────────────────────────────────▼───────────────┐
│ Phase 2: Frontend (frontend-developer)                          │
│ ┌─────────────┐    ┌──────────────┐    ┌──────────────┐       │
│ │  Setup      │───▶│ UI Components│───▶│EventSource   │       │
│ │  Next.js    │    │ (shadcn/ui)  │    │Integration   │       │
│ └─────────────┘    └──────────────┘    └──────┬───────┘       │
└────────────────────────────────────────────────┼───────────────┘
                                                  │
                         ┌────────────────────────┴────────────┐
                         │                                     │
┌────────────────────────▼─────────────────────────────────────▼──┐
│ Phase 3: Deployment (production-deployment)                     │
│ ┌─────────────┐    ┌──────────────┐    ┌──────────────┐       │
│ │  Docker     │───▶│docker-compose│───▶│  Production  │       │
│ │  Build      │    │  Setup       │    │  Deployment  │       │
│ └─────────────┘    └──────────────┘    └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

**AICODE-NOTE:** Backend must complete first because frontend needs the SSE API contract. Deployment is last because it requires both services to be functional.

---

## Development Workflow Integration

### TDD Cycle (per task)

**AICODE-NOTE:** All agents must follow Test-Driven Development workflow

```bash
# 1. Check existing AICODE comments before starting
grep -r "AICODE" web-frontend/src/
grep -r "AICODE" backend/src/

# 2. Write Tests FIRST
# - Create test file before implementation
# - Write failing tests for new functionality
# - Run tests: Verify they FAIL (red phase)

# 3. Implement Code
# - Write minimal implementation to pass tests
# - Run tests again: Iterate until PASS (green phase)

# 4. Add AICODE comments
# - Document key decisions with # AICODE-NOTE: [rationale]
# - Mark future work with # AICODE-TODO: [description]
# - Flag questions with # AICODE-ASK: [question]

# 5. Verify Tests Pass
# - Run full test suite
# - Check coverage

# 6. Commit
# - git add .
# - git commit -m "feat: [task description]"
```

### Agent-Specific Workflows

#### Frontend Developer (TypeScript + React)

```bash
cd web-frontend

# 1. Write test
npm test -- tests/unit/input-form.test.tsx

# 2. Implement component
# Edit: src/components/input-form.tsx

# 3. Run tests until green
npm test

# 4. E2E test (after backend integration)
npm run test:e2e

# 5. Commit
git add .
git commit -m "feat(frontend): add input form with validation"
```

#### Backend Developer (Python + FastAPI)

```bash
cd backend

# 1. Write test
poetry run pytest tests/test_streaming.py -v

# 2. Implement endpoint
# Edit: src/api/generate.py

# 3. Run tests until green
poetry run pytest -v

# 4. Check coverage
poetry run pytest --cov=src --cov-report=html

# 5. Commit
git add .
git commit -m "feat(backend): add SSE streaming endpoint"
```

#### Deployment (Docker)

```bash
# 1. Create Dockerfile
# Edit: backend/Dockerfile, web-frontend/Dockerfile

# 2. Test local build
docker-compose up --build

# 3. Verify health
curl http://localhost:8000/health
curl http://localhost:3000

# 4. Commit
git add .
git commit -m "feat(deploy): add Docker multi-stage builds"
```

### AICODE Comment Examples

#### TypeScript (Frontend)

```typescript
// AICODE-NOTE: Using EventSource for SSE instead of fetch for automatic reconnection
const evtSource = new EventSource(`/api/generate?topic=${topic}`);

// AICODE-NOTE: useEffect with logLines dependency ensures auto-scroll on new messages
useEffect(() => {
  logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [logLines]);

// AICODE-TODO: Add retry logic with exponential backoff for SSE errors
evtSource.onerror = (err) => {
  console.error('SSE error:', err);
  setError('Произошла ошибка потока');
};

// AICODE-ASK: Should we persist log history in localStorage for debugging?
const [logLines, setLogLines] = useState<string[]>([]);
```

#### Python (Backend)

```python
# AICODE-NOTE: Using asyncio.create_subprocess_exec instead of subprocess.Popen
# for non-blocking I/O and better async integration with FastAPI
process = await asyncio.create_subprocess_exec(
    "poetry", "run", "python", "-m", "src.ugly_script",
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)

# AICODE-NOTE: SIGTERM with 3s timeout, then SIGKILL ensures cleanup without zombies
try:
    process.send_signal(signal.SIGTERM)
    await asyncio.wait_for(process.wait(), timeout=3.0)
except asyncio.TimeoutError:
    process.kill()  # AICODE-NOTE: Force kill if graceful shutdown fails

# AICODE-TODO: Add process pool for concurrent generations (max 10 per FR)
# AICODE-ASK: Should we implement rate limiting per user/IP?
```

#### Docker (Deployment)

```dockerfile
# AICODE-NOTE: Multi-stage build reduces image size from 500MB to 150MB
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# AICODE-NOTE: Separate builder stage allows layer caching for faster rebuilds
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# AICODE-TODO: Add health check instruction for container orchestration
# HEALTHCHECK --interval=30s CMD curl -f http://localhost:3000/api/health || exit 1
```

### Logging Patterns

#### Backend (Python with Loguru)

```python
from loguru import logger

# AICODE-NOTE: Loguru provides structured logging with colors out-of-the-box
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

# Usage in code
logger.info("Starting article generation for topic: {topic}", topic=topic)
logger.success("Cached style profile found - skipping analysis")
logger.warning("Failed to fetch URL {url}: {error}", url=url, error=str(e))
logger.error("Process terminated due to client disconnect")
```

#### Frontend (TypeScript with console)

```typescript
// AICODE-NOTE: Simple console logging for development, replace with structured logger for production
const logDebug = (message: string, data?: any) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[DEBUG] ${message}`, data);
  }
};

logDebug('SSE connection established', { url: eventSourceUrl });
logDebug('Received log message', { message: event.data });
```

### AICODE Comment Check Commands

```bash
# Check all AICODE comments in project
grep -r "AICODE" web-frontend/src/ backend/src/

# Check for unresolved questions
grep -r "AICODE-ASK" web-frontend/src/ backend/src/

# Check for pending TODOs
grep -r "AICODE-TODO" web-frontend/src/ backend/src/

# Summary count
echo "Total AICODE comments: $(grep -r "AICODE" web-frontend/src/ backend/src/ | wc -l)"
echo "Pending questions: $(grep -r "AICODE-ASK" web-frontend/src/ backend/src/ | wc -l)"
echo "TODO items: $(grep -r "AICODE-TODO" web-frontend/src/ backend/src/ | wc -l)"
```

---

## Next Steps

After `/speckit.plan` completes:

1. **Review Generated Artifacts**:
   - [research.md](./research.md) - Technology decisions with AICODE rationale
   - [data-model.md](./data-model.md) - Entity definitions with validation examples
   - [contracts/](./contracts/) - API specifications
   - [quickstart.md](./quickstart.md) - Setup guide with AICODE guidelines

2. **Agent Coordination**:
   - Assign tasks to agents using TodoWrite tool
   - Start with `python-backend-developer` (Phase 1 - critical path)
   - Frontend can begin UI mockups in parallel
   - Deployment waits for Phase 1 + 2

3. **Run `/speckit.tasks`**:
   - Generate actionable task list in `tasks.md`
   - Each task will have agent assignment
   - Dependency order will be enforced

4. **Begin TDD Cycle**:
   - Follow workflow above for each task
   - Use AICODE comments for key decisions
   - Run grep checks before commits

**Estimated Timeline:**
- Phase 0 (Research): Complete ✅
- Phase 1 (Design): Complete ✅
- Phase 2 (Backend Implementation): 8-12 hours
- Phase 3 (Frontend Implementation): 6-10 hours
- Phase 4 (Deployment): 3-5 hours
- **Total**: 17-27 hours (with proper agent coordination)

**AICODE-NOTE:** Sequential phases (Backend → Frontend → Deployment) minimize integration issues. Parallel development can reduce timeline to 12-20 hours if API contract is mocked early.
