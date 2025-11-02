# TextScript Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-27

## Active Technologies

- Python 3.11+ (001-style-article-generator, 002-web-frontend-docker/backend)
- TypeScript 5.x + Next.js 14 (002-web-frontend-docker/frontend)

## Project Structure

```text
src/                  # Python article generation script
tests/                # Python tests

web-frontend/         # Next.js frontend (NEW in 002)
├── app/             # Next.js App Router
├── components/      # React components + shadcn/ui
└── tests/           # Frontend tests

backend/             # FastAPI backend (NEW in 002)
├── src/             # FastAPI app + services
└── tests/           # Backend tests
```

## Commands

### Python (Article Script & Backend)
```bash
cd src && poetry run python -m src.ugly_script
cd backend && poetry run uvicorn src.main:app --reload
pytest
ruff check .
```

### Frontend (Next.js)
```bash
cd web-frontend && npm run dev
cd web-frontend && npm test
cd web-frontend && npm run build
```

### Docker
```bash
docker-compose up --build
docker-compose -f docker-compose.dev.yml up
```

## Code Style

- Python 3.11+: Follow standard conventions, use Pydantic for validation
- TypeScript: Strict mode, ESLint + Prettier
- React: Functional components, hooks, shadcn/ui components
- Tailwind: Utility-first classes, zinc palette for dark theme

## QA Automation

### Automated Testing & Fixing Cycles

Run comprehensive E2E testing with automated bug fixing:

```bash
/qa-cycle
```

**What it does:**
1. Tests application against specification (specs/*/spec.md)
2. Finds bugs and categorizes them (frontend/backend/design)
3. Delegates fixes to specialist agents
4. Deploys to production (with confirmation)
5. Repeats until all tests pass

**Parameters:**
- `url` - Application URL (default: auto-detect)
- `spec_path` - Specification path (default: auto-detect)
- `max_iterations` - Max test-fix cycles (default: 3)

**Test Reports:** `test-reports/qa-report-iteration-*.md`

**Documentation:** See [QA_WORKFLOW.md](./QA_WORKFLOW.md) for details.

## Recent Changes

- 2025-11-02: Added QA Automation system with /qa-cycle command
- 002-web-frontend-docker: Added Next.js frontend, FastAPI backend, Docker deployment
- 001-style-article-generator: Added Python 3.11+

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
