# Quickstart: Web Frontend with Docker Deployment

**Feature**: 002-web-frontend-docker
**Last Updated**: 2025-10-27

## Prerequisites

- **Node.js**: 20.x or later
- **Python**: 3.11+
- **Poetry**: Latest version
- **Docker**: 24.x+ with Docker Compose
- **Git**: For version control

## Project Setup

### 1. Initial Repository Structure

```bash
# From repository root
cd /Users/teterinsa/Projects/TextScript

# Ensure you're on the feature branch
git checkout 002-web-frontend-docker
```

Current structure:
```
TextScript/
├── src/              # Existing Python script
├── pyproject.toml    # Existing dependencies
└── specs/002-web-frontend-docker/  # This feature's docs
```

### 2. Create Frontend Project

```bash
# Create Next.js app with TypeScript
npx create-next-app@latest web-frontend \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir \
  --import-alias "@/*"

cd web-frontend

# Initialize shadcn/ui
npx shadcn-ui@latest init

# When prompted:
# - Style: Default
# - Base color: Zinc
# - CSS variables: Yes

# Install required shadcn components
npx shadcn-ui@latest add button card input textarea label checkbox alert tabs

# Install additional dependencies
npm install next-themes lucide-react
```

### 3. Create Backend Project

```bash
# From repository root
mkdir -p backend/src/api backend/src/services backend/tests
cd backend

# Initialize Python package
cat > pyproject.toml << EOF
[tool.poetry]
name = "textscript-backend"
version = "0.1.0"
description = "FastAPI backend for TextScript article generator"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.100.0"
uvicorn = {extras = ["standard"], version = "^0.23.0"}

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
httpx = "^0.24.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

# Install dependencies
poetry install
```

## Development Workflow

### Option A: Local Development (Without Docker)

#### 1. Terminal 1: Backend

```bash
cd backend

# Set environment
export PYTHONUNBUFFERED=1
export SCRIPT_PATH=../src  # Path to existing script

# Run FastAPI dev server
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

#### 2. Terminal 2: Frontend

```bash
cd web-frontend

# Set API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run Next.js dev server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Option B: Docker Development

#### 1. Create docker-compose.dev.yml

```yaml
version: '3.9'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
      target: development
    ports:
      - "8000:8000"
    volumes:
      - ./backend/src:/app/backend/src
      - ./src:/app/src:ro
    environment:
      - PYTHONUNBUFFERED=1
      - RELOAD=true

  frontend:
    build:
      context: ./web-frontend
      dockerfile: Dockerfile
      target: development
    ports:
      - "3000:3000"
    volumes:
      - ./web-frontend/src:/app/src
      - ./web-frontend/public:/app/public
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
```

#### 2. Run with Docker Compose

```bash
# From repository root
docker-compose -f docker-compose.dev.yml up --build

# Or detached
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs -f
```

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_streaming.py -v
```

### Frontend Tests

```bash
cd web-frontend

# Run unit tests
npm test

# Run E2E tests (requires running backend)
npm run test:e2e

# Run with coverage
npm test -- --coverage
```

## Manual Testing

### 1. Test SSE Streaming

```bash
# Start backend (if not running)
cd backend
poetry run uvicorn src.main:app --reload

# In another terminal, test with curl
curl -N "http://localhost:8000/api/generate?topic=Test&source_urls=https://example.com&research=false"

# Expected output:
# data: [INFO] Starting article generation...
# data: [INFO] Successfully fetched: https://example.com
# event: result
# data: <article content>
# event: close
# data: done
```

### 2. Test Frontend Flow

1. Open `http://localhost:3000`
2. Enter topic: "Machine Learning Basics"
3. Enter URL: `https://example.com/ml-article`
4. Check "Enable Research" (optional)
5. Click "Сгенерировать"
6. Verify:
   - Button becomes disabled with spinner
   - Execution card appears
   - Logs stream in real-time
   - Auto-scroll works
   - Result tab enables when done
   - Copy/Download buttons work

### 3. Test Error Handling

**Invalid URL:**
```bash
curl -N "http://localhost:8000/api/generate?topic=Test&source_urls=not-a-url"
# Expected: 400 validation error
```

**Unreachable URL:**
- Use `https://httpbin.org/delay/60` (will timeout)
- Expected: Warning in logs, generation continues

**Client Disconnect:**
- Start generation, close browser tab immediately
- Backend should log process termination (check logs)

## Code Structure Examples

### Backend: main.py

```python
# backend/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.generate import router as generate_router

app = FastAPI(title="TextScript API", version="1.0.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Backend: SSE Endpoint Skeleton

```python
# backend/src/api/generate.py
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import asyncio

router = APIRouter()

@router.get("/generate")
async def generate_article(
    topic: str = Query(..., min_length=1),
    source_urls: str = Query(...),  # Comma-separated
    research: bool = Query(default=False),
):
    async def event_stream():
        # TODO: Implement subprocess spawning
        # TODO: Stream stdout as SSE messages
        # TODO: Handle process cleanup on disconnect
        yield f"data: [INFO] Starting generation...\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )
```

### Frontend: Page Component Skeleton

```typescript
// web-frontend/app/page.tsx
'use client';

import { useState } from 'react';
import { InputForm } from '@/components/input-form';
import { ExecutionView } from '@/components/execution-view';

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(false);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [finalArticle, setFinalArticle] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (data: { topic: string; urls: string; research: boolean }) => {
    // TODO: Create EventSource
    // TODO: Handle messages, result, error, close events
  };

  return (
    <main className="container max-w-3xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">TextScript</h1>

      <InputForm onSubmit={handleSubmit} disabled={isLoading} />

      {isLoading && (
        <ExecutionView
          logLines={logLines}
          result={finalArticle}
          error={error}
        />
      )}
    </main>
  );
}
```

## Debugging Tips

### 1. Backend Logs

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
poetry run uvicorn src.main:app --reload --log-level debug
```

### 2. Frontend Network Tab

- Open DevTools → Network tab
- Filter by `generate` to see SSE connection
- Check "Event Stream" tab for real-time events

### 3. Process Tracking

```bash
# List Python processes
ps aux | grep "python.*ugly_script"

# Monitor process count
watch -n 1 'ps aux | grep python | wc -l'
```

### 4. Docker Logs

```bash
# Follow logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Check specific container
docker logs textscript-backend-1 --tail 100 -f
```

## Common Issues

### Issue: SSE Connection Immediately Closes

**Cause**: CORS or network issue

**Solution**:
```python
# backend/src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

### Issue: Logs Not Auto-Scrolling

**Cause**: useEffect dependency issue

**Solution**:
```typescript
// Ensure logLines is in dependency array
useEffect(() => {
  logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [logLines]); // <- Must include logLines
```

### Issue: Process Not Terminating on Tab Close

**Cause**: Missing disconnect detection

**Solution**:
```python
from fastapi import Request

async def generate_article(request: Request, ...):
    while not await request.is_disconnected():
        # Check every iteration
        ...
```

## AICODE Comment Guidelines

**IMPORTANT**: This project uses AICODE comments to document key technical decisions.

### Comment Types

```typescript
// AICODE-NOTE: Document why a specific approach was chosen
// Example: Using EventSource for automatic reconnection handling

// AICODE-TODO: Mark future improvements or optimizations
// Example: Add retry logic with exponential backoff

// AICODE-ASK: Flag questions that need clarification
// Example: Should we cache API responses in localStorage?
```

### When to Add AICODE Comments

**DO add AICODE comments for:**
- ✅ Critical technical decisions (why EventSource vs WebSocket?)
- ✅ Non-obvious implementations (zombie process prevention logic)
- ✅ Performance optimizations (multi-stage Docker builds)
- ✅ Workarounds or temporary solutions (mark with TODO)
- ✅ Questions that need team discussion (ASK)

**DON'T add AICODE comments for:**
- ❌ Self-explanatory code (`const name = "John"`)
- ❌ Every single line (creates noise)
- ❌ Standard patterns (basic useState hooks)

### Frontend Example (TypeScript)

```typescript
// components/execution-view.tsx
export function ExecutionView({ logLines }: Props) {
  const logEndRef = useRef<HTMLDivElement>(null);

  // AICODE-NOTE: useEffect with logLines dependency ensures auto-scroll
  // on new messages without manual scrollTop manipulation
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logLines]);

  // AICODE-TODO: Add virtualization for logs > 1000 lines (performance)
  return (
    <pre className="max-h-60 overflow-y-auto">
      {logLines.map((line, idx) => (
        <div key={idx}>{line}</div>
      ))}
      <div ref={logEndRef} />  {/* Scroll anchor */}
    </pre>
  );
}
```

### Backend Example (Python)

```python
# backend/src/services/process_manager.py
class ProcessManager:
    def __init__(self):
        # AICODE-NOTE: Track processes for cleanup and monitoring
        self.active_processes: dict[str, Process] = {}

    async def cleanup_process(self, process: Process):
        if process.returncode is None:
            # AICODE-NOTE: SIGTERM allows graceful shutdown (3s timeout)
            # before SIGKILL - prevents zombie processes (FR-016.2)
            process.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                # AICODE-NOTE: Force kill if graceful shutdown fails
                process.kill()

        # AICODE-TODO: Add Prometheus metrics for process lifecycle
```

### Checking AICODE Comments

```bash
# Find all AICODE comments
grep -r "AICODE" web-frontend/src/ backend/src/

# Find unresolved questions (need team input)
grep -r "AICODE-ASK" web-frontend/src/ backend/src/

# Find pending TODOs (future work)
grep -r "AICODE-TODO" web-frontend/src/ backend/src/

# Count summary
echo "Total: $(grep -r "AICODE" web-frontend/src/ backend/src/ | wc -l)"
echo "Questions: $(grep -r "AICODE-ASK" web-frontend/src/ backend/src/ | wc -l)"
echo "TODOs: $(grep -r "AICODE-TODO" web-frontend/src/ backend/src/ | wc -l)"
```

### Integration with TDD Workflow

```bash
# Before implementing a task:
# 1. Check existing AICODE comments in related files
grep -r "AICODE" web-frontend/src/components/input-form.tsx

# 2. Write tests (TDD: Red phase)
npm test -- tests/unit/input-form.test.tsx

# 3. Implement code (TDD: Green phase)
# - Add AICODE comments for key decisions
# - Mark future improvements with TODO
# - Flag questions with ASK

# 4. Verify tests pass
npm test

# 5. Commit with AICODE grep check
grep -r "AICODE-ASK" web-frontend/src/ && echo "⚠️ Unresolved questions!"
git add .
git commit -m "feat: implement input validation with AICODE docs"
```

---

## Next Steps

After setup:

1. **Implement FR-001 to FR-005**: Basic UI structure
2. **Implement FR-016 to FR-021**: Backend SSE streaming
3. **Implement FR-004.1**: Form disabling logic
4. **Implement FR-017.1, FR-018.1**: Graceful URL failures
5. **Implement FR-016.1, FR-016.2**: Zombie process prevention
6. **Add tests**: Unit + integration coverage
7. **Docker production build**: Multi-stage Dockerfile
8. **Deployment**: Production server setup

**IMPORTANT**: Follow TDD workflow and add AICODE comments for key decisions.

Refer to [tasks.md](./tasks.md) (generated by `/speckit.tasks`) for detailed implementation checklist.

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Server-Sent Events MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [OpenAPI Specification](./contracts/api-spec.yaml)
- [Data Model](./data-model.md)
- [Research & Decisions](./research.md)
