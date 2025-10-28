# Research: Web Frontend with Docker Deployment

**Feature**: 002-web-frontend-docker
**Date**: 2025-10-27
**Status**: Complete

## Overview

This document captures technical research and design decisions for building a production-ready web UI for the existing Python article generation script. Focus areas: SSE streaming, process lifecycle management, UI framework selection, and containerization.

---

## R1: Server-Sent Events (SSE) Implementation

### Decision
Use **native EventSource API** on frontend with **FastAPI StreamingResponse** on backend.

### Rationale
- **Simplicity**: SSE is HTTP-based, no WebSocket complexity
- **Browser support**: EventSource API is standard in all modern browsers
- **One-way streaming**: Perfect fit for log streaming (server→client only)
- **Auto-reconnect**: EventSource handles reconnection automatically
- **FastAPI support**: `StreamingResponse` with `text/event-stream` media type

### Implementation Pattern

**Backend (FastAPI)**:
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

async def generate_stream():
    # Read subprocess stdout line-by-line
    while line := await process.stdout.readline():
        yield f"data: {line.decode()}\n\n"

    # Send custom event for result
    yield f"event: result\ndata: {article_text}\n\n"
    yield f"event: close\ndata: done\n\n"

@app.get("/api/generate")
async def stream_endpoint():
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**Frontend (Next.js)**:
```typescript
// AICODE-NOTE: EventSource API provides automatic reconnection on network errors
const evtSource = new EventSource('/api/generate?topic=...');

// AICODE-NOTE: onmessage handles default "message" events (log lines from backend)
evtSource.onmessage = (event) => {
  setLogLines(prev => [...prev, event.data]);
};

// AICODE-NOTE: Custom event listeners for structured data (result, error, close)
evtSource.addEventListener('result', (event) => {
  setFinalArticle(event.data);
});

evtSource.addEventListener('close', () => {
  evtSource.close();  // AICODE-NOTE: Cleanup to prevent memory leaks
  setIsLoading(false);
});
```

### Alternatives Considered
- **WebSockets**: Bidirectional, but overkill for one-way streaming. More complex error handling.
- **Long polling**: Higher latency, more resource-intensive than SSE.
- **HTTP/2 Server Push**: Deprecated in many browsers, poor compatibility.

### References
- [MDN: Using Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [FastAPI StreamingResponse docs](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)

---

## R2: Subprocess Lifecycle Management (Zombie Prevention)

### Decision
Implement **process tracking with SIGTERM on disconnect** using FastAPI middleware and asyncio.

### Rationale
- **Critical requirement**: FR-016.1, FR-016.2 mandate zombie prevention
- **Resource protection**: Prevents wasted CPU and LLM tokens when user closes tab
- **FastAPI context managers**: `asynccontextmanager` for cleanup on disconnect
- **Python signals**: SIGTERM for graceful shutdown, SIGKILL as fallback

### Implementation Pattern

```python
from fastapi import Request
from contextlib import asynccontextmanager
import signal

class ProcessManager:
    def __init__(self):
        # AICODE-NOTE: Track all active processes for monitoring and cleanup
        self.active_processes = {}

    async def track_process(self, request_id: str, process):
        self.active_processes[request_id] = process
        try:
            yield process
        finally:
            # AICODE-NOTE: Cleanup on disconnect - critical for zombie prevention (FR-016.2)
            if process.returncode is None:
                # AICODE-NOTE: SIGTERM allows graceful shutdown (3s timeout)
                process.send_signal(signal.SIGTERM)
                try:
                    await asyncio.wait_for(process.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    # AICODE-NOTE: Force kill if graceful shutdown fails
                    process.kill()
            del self.active_processes[request_id]

@app.get("/api/generate")
async def stream_endpoint(request: Request):
    request_id = str(uuid.uuid4())

    # AICODE-NOTE: asyncio.create_subprocess_exec for non-blocking I/O
    process = await asyncio.create_subprocess_exec(
        "poetry", "run", "python", "-m", "src.ugly_script",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async with process_manager.track_process(request_id, process):
        # AICODE-NOTE: Check disconnect every iteration to detect tab close (SC-012)
        while not await request.is_disconnected():
            line = await process.stdout.readline()
            if not line:
                break
            yield f"data: {line.decode()}\n\n"
```

### Key Features
1. **Disconnect detection**: `request.is_disconnected()` checks SSE client status
2. **Graceful shutdown**: SIGTERM → wait 3s → SIGKILL if needed
3. **Process registry**: Track all active processes for debugging/monitoring
4. **Cleanup guarantee**: Context manager ensures cleanup on any exit path

### Alternatives Considered
- **No tracking**: Simplest but creates zombie processes (rejected per spec)
- **Timeout only**: Doesn't handle user tab close (insufficient)
- **External process monitor**: Added complexity, harder to debug

### References
- [Python asyncio subprocess docs](https://docs.python.org/3/library/asyncio-subprocess.html)
- [FastAPI Request.is_disconnected()](https://github.com/tiangolo/fastapi/discussions/8856)

---

## R3: Graceful URL Failure Handling

### Decision
Implement **try-except per URL** in existing script with warning logs, continue execution.

### Rationale
- **Requirement**: FR-017.1, FR-018.1 mandate continuation on URL failure
- **User experience**: Better to get partial results than complete failure
- **Observability**: Warning logs clearly show which URLs failed and why

### Implementation Pattern

**Modify existing script** (minimal changes):
```python
def fetch_style_urls(urls: list[str]) -> list[str]:
    """Fetch URLs with graceful degradation."""
    successful_content = []

    # AICODE-NOTE: Process URLs sequentially to maintain predictable logging order
    for url in urls:
        try:
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
            successful_content.append(response.text)
            print(f"[INFO] Successfully fetched: {url}")
        except httpx.TimeoutException:
            # AICODE-NOTE: Specific timeout handling for FR-017.1
            print(f"[WARN] Не удалось получить URL: {url} (Ошибка: Таймаут)")
        except httpx.HTTPStatusError as e:
            # AICODE-NOTE: HTTP errors (404, 503) should not fail entire generation
            print(f"[WARN] Не удалось получить URL: {url} (Ошибка: {e.response.status_code})")
        except Exception as e:
            # AICODE-NOTE: Catch-all for network errors, DNS failures, etc.
            print(f"[WARN] Не удалось получить URL: {url} (Ошибка: {str(e)})")

    # AICODE-NOTE: Fail only if ALL URLs failed - need at least one for style analysis
    if not successful_content:
        print("[ERROR] Не удалось загрузить ни одного URL для стиля")
        raise ValueError("All style URLs failed")

    return successful_content
```

### Key Features
1. **Granular error handling**: Timeout, HTTP errors, network errors separately logged
2. **Russian messages**: Match user's language preference (from spec example)
3. **Fail-safe**: Only error if ALL URLs fail (at least one needed for style)
4. **Log format**: `[WARN]` prefix for easy filtering in frontend

### Alternatives Considered
- **Fail-fast**: Simple but poor UX (rejected per spec)
- **Retry logic**: Adds latency without guarantees (not needed for v1)
- **Parallel fetching**: Faster but harder to debug (defer to v2)

---

## R4: Next.js + shadcn/ui Architecture

### Decision
Use **Next.js 14 App Router** with **shadcn/ui** and **Tailwind CSS**.

### Rationale
- **User requirement**: Explicitly requested shadcn, Tailwind, Next.js
- **App Router benefits**: Built-in streaming, server components, better SEO
- **shadcn/ui philosophy**: Copy-paste components (no npm dependency), full customization
- **Tailwind utility-first**: Rapid development, consistent design system
- **TypeScript**: Type safety for complex state management

### Component Architecture

```typescript
// app/page.tsx - Main page (Server Component by default)
export default function HomePage() {
  return (
    <main className="container max-w-3xl mx-auto py-8">
      <Header />
      <GenerationInterface /> {/* Client Component */}
    </main>
  );
}

// components/generation-interface.tsx - Client Component
'use client';

export function GenerationInterface() {
  const [isLoading, setIsLoading] = useState(false);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [finalArticle, setFinalArticle] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  return (
    <>
      <InputForm onSubmit={handleSubmit} disabled={isLoading} />
      {isLoading && (
        <ExecutionView
          logLines={logLines}
          result={finalArticle}
          error={error}
        />
      )}
    </>
  );
}
```

### shadcn/ui Component Selection
Required components (install via CLI):
```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input textarea label checkbox alert tabs
```

These provide:
- **Accessible**: ARIA attributes, keyboard navigation
- **Customizable**: Tailwind classes, easy overrides
- **Consistent**: Unified design tokens (zinc palette for dark theme)

### Theme Implementation
```typescript
// app/layout.tsx
import { ThemeProvider } from 'next-themes';

export default function RootLayout({ children }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}

// tailwind.config.ts
export default {
  darkMode: ["class"],
  theme: {
    extend: {
      colors: {
        // Zinc palette for dark theme (Linear/Vercel style)
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // ... other tokens
      },
    },
  },
};
```

### Alternatives Considered
- **Vite + React**: Faster dev build, but no SSR (Next.js needed for production)
- **Material UI / Ant Design**: Heavier, less customizable than shadcn/ui
- **Vanilla CSS**: More control but slower development

### References
- [Next.js 14 App Router docs](https://nextjs.org/docs/app)
- [shadcn/ui documentation](https://ui.shadcn.com/)
- [Tailwind CSS docs](https://tailwindcss.com/docs)

---

## R5: Docker Multi-Service Deployment

### Decision
Use **Docker Compose** with **multi-stage builds** for development and production.

### Rationale
- **Requirement**: FR-022, FR-023 mandate Docker deployment
- **Multi-service**: Frontend (Next.js) + Backend (FastAPI) + shared volumes
- **Development parity**: Same environment locally and in production
- **Build optimization**: Multi-stage reduces image size (Next.js: ~500MB → ~150MB)

### Architecture

```yaml
# docker-compose.yml
version: '3.9'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src:ro          # Existing script (read-only)
      - ./pyproject.toml:/app/pyproject.toml:ro
    environment:
      - PYTHONUNBUFFERED=1
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./web-frontend
      dockerfile: Dockerfile
      target: production           # Multi-stage target
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  # Development override: docker-compose.override.yml
  # (Hot reload, source mounts)
```

### Multi-Stage Dockerfile (Frontend)

```dockerfile
# web-frontend/Dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]

FROM node:20-alpine AS development
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

### Key Features
1. **Layer caching**: Dependencies cached separately from source
2. **Size optimization**: Production image ~150MB (vs ~500MB single-stage)
3. **Security**: Non-root user, minimal base image (alpine)
4. **Development mode**: Source mount + hot reload for rapid iteration

### Deployment Workflow
```bash
# Development
docker-compose up

# Production build
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml up -d

# Deploy to server
docker save textscript-frontend | ssh server docker load
```

### Alternatives Considered
- **Single Dockerfile**: Simpler but larger images, slower builds
- **Kubernetes**: Overkill for single-server deployment
- **Separate containers per service**: More flexible but complex networking

### References
- [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Next.js Docker deployment](https://nextjs.org/docs/deployment#docker-image)
- [FastAPI Docker guide](https://fastapi.tiangolo.com/deployment/docker/)

---

## R6: State Management & Auto-Scroll

### Decision
Use **React useState** with **useEffect ref scrolling** (no external state library).

### Rationale
- **Simplicity**: Feature has simple, local state (no global state needed)
- **Performance**: useState is sufficient for ~500 log lines
- **Auto-scroll requirement**: FR-007 mandates auto-scroll on new logs
- **Ref-based scrolling**: Reliable, doesn't trigger re-renders

### Implementation Pattern

```typescript
// components/execution-view.tsx
'use client';

import { useEffect, useRef } from 'react';

export function ExecutionView({ logLines }: { logLines: string[] }) {
  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logLines]);

  return (
    <TabsContent value="log">
      <pre className="max-h-60 overflow-y-auto bg-zinc-900 p-4 rounded">
        {logLines.map((line, idx) => (
          <div key={idx}>{line}</div>
        ))}
        <div ref={logEndRef} />  {/* Scroll anchor */}
      </pre>
    </TabsContent>
  );
}
```

### Key Features
1. **Smooth scrolling**: `behavior: 'smooth'` for better UX
2. **Performance**: Only scrolls on logLines change (not every render)
3. **Scroll anchor**: Empty div at bottom acts as scroll target
4. **Max height**: `max-h-60` (~15rem) prevents page stretching

### Alternatives Considered
- **Zustand/Redux**: Overkill for local component state
- **IntersectionObserver**: More complex, not needed for always-scroll
- **Manual scrollTop**: Works but less declarative than ref + useEffect

---

## R7: Input Validation Strategy

### Decision
Implement **controlled inputs with derived disabled state** (no external validation library).

### Rationale
- **Requirements**: FR-003, FR-003.1, FR-003.2 mandate dual-field validation
- **Simplicity**: Native HTML5 validation + React controlled components
- **Performance**: No validation library overhead
- **UX**: Button disabled state provides immediate feedback

### Implementation Pattern

```typescript
export function InputForm({ onSubmit, disabled }: InputFormProps) {
  // AICODE-NOTE: Controlled components for React state as single source of truth
  const [topic, setTopic] = useState('');
  const [urls, setUrls] = useState('');
  const [research, setResearch] = useState(false);

  // AICODE-NOTE: Derived validation state - no external library needed (FR-003.2)
  // trim() prevents empty-looking filled fields
  const isFormValid = topic.trim().length > 0 && urls.trim().length > 0;
  const isSubmitDisabled = !isFormValid || disabled;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    // AICODE-NOTE: Double-check validation before submit (defense in depth)
    if (isFormValid && !disabled) {
      onSubmit({ topic, urls, research });
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Textarea
        value={urls}
        onChange={(e) => setUrls(e.target.value)}
        disabled={disabled}  // AICODE-NOTE: Prevents concurrent requests (FR-004.1)
        placeholder="https://example.com/article1"
        required
      />
      <Input
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        disabled={disabled}  // AICODE-NOTE: Disabled during generation
        placeholder="Machine Learning Basics"
        required
      />
      <Checkbox
        checked={research}
        onCheckedChange={setResearch}
        disabled={disabled}  // AICODE-NOTE: All inputs disabled together (FR-004.1)
      />
      <Button type="submit" disabled={isSubmitDisabled}>
        {/* AICODE-NOTE: Visual feedback - spinner during loading */}
        {disabled ? <Loader2 className="animate-spin" /> : 'Сгенерировать'}
      </Button>
    </form>
  );
}
```

### Key Features
1. **Controlled components**: React state as single source of truth
2. **Derived validation**: `isFormValid` computed from state (no separate validation step)
3. **Trim whitespace**: Prevents empty-looking filled fields
4. **Loading state**: All fields disabled during generation (FR-004.1)
5. **Visual feedback**: Loader icon on button when disabled

### Validation Rules
- **Topic**: Non-empty after trim
- **URLs**: Non-empty after trim (format validation deferred to backend)
- **Both required**: Button stays disabled until both filled
- **All disabled**: During loading (prevents concurrent submissions)

### Alternatives Considered
- **react-hook-form**: Powerful but overkill for 2 simple fields
- **Zod schema validation**: Type-safe but adds complexity
- **Server-side only**: Poor UX (requires network round-trip)

---

## Summary of Key Decisions

| Area | Decision | Primary Rationale |
|------|----------|-------------------|
| Streaming | EventSource + FastAPI SSE | Simple, native browser support, perfect for one-way logs |
| Process Management | asyncio subprocess + SIGTERM on disconnect | Prevents zombie processes (critical req FR-016.2) |
| URL Failures | Try-except per URL, log warnings | Graceful degradation (FR-017.1, SC-011) |
| Frontend Framework | Next.js 14 App Router | User requirement + SSR + streaming |
| UI Library | shadcn/ui + Tailwind | User requirement + customization + accessibility |
| Containerization | Docker Compose + multi-stage | Production requirement (FR-022) + optimization |
| State Management | React useState + refs | Sufficient for local state, no library needed |
| Input Validation | Controlled inputs + derived state | Simple, performant, immediate feedback |

---

## Open Questions / Future Enhancements

1. **Horizontal scaling**: Current design is single-server. If needed:
   - Add Redis for process tracking across instances
   - Use sticky sessions or process-pinning

2. **Authentication**: Not in v1 scope. If needed:
   - Add next-auth for frontend
   - JWT tokens for backend API

3. **Persistent storage**: Currently file-based (topic.txt, output.txt). If needed:
   - PostgreSQL for generation history
   - S3/blob storage for large outputs

4. **Monitoring**: Add observability in production:
   - Prometheus metrics (active processes, generation time)
   - Structured logging (JSON format)
   - Health check endpoints

These are deferred to future iterations per YAGNI principle. Current design supports these additions without major refactoring.
