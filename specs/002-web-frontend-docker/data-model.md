# Data Model: Web Frontend with Docker Deployment

**Feature**: 002-web-frontend-docker
**Date**: 2025-10-27
**Status**: Complete

## Overview

This feature has minimal persistent data requirements. All data flows through the request-response cycle with temporary file storage. This document defines the data structures used for API contracts, frontend state, and inter-process communication.

---

## DM-1: Generation Request

Represents a user's article generation request with all input parameters.

### Fields

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `topic` | `string` | Yes | Non-empty, max 1000 chars | Article topic/title to generate |
| `source_urls` | `string[]` | Yes | Non-empty array, valid URLs | Style reference URLs |
| `research_enabled` | `boolean` | No | Default: `false` | Enable research mode flag |

### Validation Rules

1. **topic**:
   - Must not be empty or whitespace-only
   - Maximum length: 1000 characters
   - Supports UTF-8 (Cyrillic, emoji, etc.)

2. **source_urls**:
   - Array must contain at least 1 URL
   - Each URL must be well-formed (http/https)
   - Maximum 10 URLs per request (prevents abuse)
   - Individual URL max length: 2048 chars

3. **research_enabled**:
   - Boolean flag (true/false)
   - Optional, defaults to false if not provided

### TypeScript Type

```typescript
// AICODE-NOTE: Simple interface for frontend - validation happens on backend
interface GenerationRequest {
  topic: string;
  source_urls: string[];  // AICODE-NOTE: Array of URLs, not validated client-side
  research_enabled?: boolean;  // AICODE-NOTE: Optional, defaults to false
}
```

### Python Model (Pydantic)

```python
from pydantic import BaseModel, Field, HttpUrl

# AICODE-NOTE: Pydantic provides automatic validation for API inputs (FR-003, FR-003.1)
class GenerationRequest(BaseModel):
    # AICODE-NOTE: min_length/max_length prevent empty topics and DoS via huge inputs
    topic: str = Field(..., min_length=1, max_length=1000)

    # AICODE-NOTE: HttpUrl validates URL format, min/max items prevent abuse
    source_urls: list[HttpUrl] = Field(..., min_items=1, max_items=10)

    research_enabled: bool = Field(default=False)
```

### Example

```json
{
  "topic": "Основы машинного обучения",
  "source_urls": [
    "https://example.com/ml-intro",
    "https://another.com/ml-guide"
  ],
  "research_enabled": true
}
```

---

## DM-2: Log Message

Represents a single line of output from the generation process, streamed via SSE.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `level` | `"INFO" \| "WARN" \| "ERROR"` | Yes | Log severity level |
| `message` | `string` | Yes | Log message text |
| `timestamp` | `string (ISO 8601)` | No | Message timestamp (optional) |

### Format

**Plain text (default SSE message)**:
```
data: [INFO] Successfully fetched: https://example.com
```

**Structured (optional, for future enhancement)**:
```json
data: {"level": "INFO", "message": "Successfully fetched: https://example.com", "timestamp": "2025-10-27T10:30:45Z"}
```

### Log Level Meanings

- **INFO**: Normal operation progress (URL fetched, step completed)
- **WARN**: Non-fatal issue (URL failed but continuing, partial data)
- **ERROR**: Fatal error (script crashed, all URLs failed)

### TypeScript Type

```typescript
interface LogMessage {
  level: 'INFO' | 'WARN' | 'ERROR';
  message: string;
  timestamp?: string;
}

// Frontend state: array of raw strings (simplest)
type LogLines = string[];
```

### Example Messages

```
[INFO] Starting article generation...
[INFO] Successfully fetched: https://example.com/article1
[WARN] Не удалось получить URL: https://unreachable.com (Ошибка: Таймаут)
[INFO] Research enabled, performing deep analysis...
[INFO] Generation complete (45 seconds)
```

---

## DM-3: Generated Article

Represents the final article output when generation succeeds.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | `string` | Yes | Article markdown/text content |
| `metadata` | `ArticleMetadata` | No | Generation metadata (optional) |

### Metadata Fields (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `generation_time_seconds` | `number` | Total generation duration |
| `research_used` | `boolean` | Whether research was enabled |
| `urls_fetched` | `number` | Number of successfully fetched URLs |
| `total_urls` | `number` | Total URLs provided |

### Constraints

- **content**: Maximum 50,000 characters (per SC-008)
- **content**: UTF-8 encoded text (may contain Markdown formatting)

### TypeScript Type

```typescript
interface ArticleMetadata {
  generation_time_seconds?: number;
  research_used?: boolean;
  urls_fetched?: number;
  total_urls?: number;
}

interface GeneratedArticle {
  content: string;
  metadata?: ArticleMetadata;
}
```

### SSE Event Format

Custom event `result`:
```
event: result
data: # Основы машинного обучения\n\nМашинное обучение (ML) — это раздел...
```

Or with metadata (JSON):
```
event: result
data: {"content": "# Article text...", "metadata": {"generation_time_seconds": 45, "urls_fetched": 2, "total_urls": 2}}
```

---

## DM-4: Error Response

Represents error conditions during generation or validation.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error_type` | `"validation" \| "process" \| "timeout" \| "unknown"` | Yes | Error category |
| `message` | `string` | Yes | User-friendly error description |
| `details` | `string` | No | Technical details (for debugging) |

### Error Types

- **validation**: Invalid input (empty fields, bad URLs)
- **process**: Script execution failed (non-zero exit code)
- **timeout**: Generation exceeded time limit
- **unknown**: Unexpected error

### TypeScript Type

```typescript
interface ErrorResponse {
  error_type: 'validation' | 'process' | 'timeout' | 'unknown';
  message: string;
  details?: string;
}
```

### Python Model

```python
class ErrorResponse(BaseModel):
    error_type: Literal["validation", "process", "timeout", "unknown"]
    message: str
    details: Optional[str] = None
```

### SSE Error Event

Custom event `error`:
```
event: error
data: {"error_type": "process", "message": "Script crashed with exit code 1", "details": "ValueError: All style URLs failed"}
```

---

## DM-5: User Session State (Frontend Only)

Ephemeral frontend state for a single browser session. Not persisted.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `isLoading` | `boolean` | Whether generation is in progress |
| `logLines` | `string[]` | Accumulated log messages |
| `finalArticle` | `string \| null` | Generated article (when complete) |
| `error` | `string \| null` | Error message (if failed) |
| `theme` | `"light" \| "dark"` | Current theme preference |

### State Transitions

```
Initial → Loading → Success
                  → Error

States:
- Initial:  { isLoading: false, logLines: [], finalArticle: null, error: null }
- Loading:  { isLoading: true, logLines: [...], finalArticle: null, error: null }
- Success:  { isLoading: false, logLines: [...], finalArticle: "...", error: null }
- Error:    { isLoading: false, logLines: [...], finalArticle: null, error: "..." }
```

### TypeScript Type

```typescript
// AICODE-NOTE: Frontend state machine - ephemeral, not persisted except theme
interface UserSessionState {
  isLoading: boolean;  // AICODE-NOTE: Controls UI state (disabled inputs, spinner)
  logLines: string[];  // AICODE-NOTE: Accumulated SSE messages, no limit in v1
  finalArticle: string | null;  // AICODE-NOTE: null until generation completes
  error: string | null;  // AICODE-NOTE: Mutually exclusive with finalArticle
  theme: 'light' | 'dark';  // AICODE-NOTE: Only field persisted to localStorage
}
```

### Persistence

- **theme**: Stored in `localStorage` (key: `theme`)
- **All other fields**: Ephemeral, cleared on page refresh

---

## DM-6: Process Tracking (Backend Only)

Internal backend data structure for managing subprocess lifecycle.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | `string (UUID)` | Unique identifier for this generation request |
| `process` | `asyncio.subprocess.Process` | Subprocess handle |
| `started_at` | `datetime` | Process start timestamp |
| `client_connected` | `boolean` | Whether SSE client is still connected |

### Purpose

Used by `ProcessManager` service to:
- Track active processes
- Detect disconnected clients
- Send SIGTERM/SIGKILL on cleanup

### Python Type

```python
from dataclasses import dataclass
from datetime import datetime
import asyncio

# AICODE-NOTE: Internal tracking structure for zombie process prevention (FR-016.2)
@dataclass
class ProcessTracker:
    request_id: str  # AICODE-NOTE: UUID for correlation in logs and debugging
    process: asyncio.subprocess.Process  # AICODE-NOTE: Subprocess handle for cleanup
    started_at: datetime  # AICODE-NOTE: Track process age for timeout logic
    client_connected: bool = True  # AICODE-NOTE: Detect tab close for cleanup trigger
```

### Lifecycle

1. **Created**: When SSE connection starts
2. **Tracked**: Added to `active_processes` dict
3. **Monitored**: Check `client_connected` each iteration
4. **Cleaned**: On disconnect or completion, send SIGTERM → wait → SIGKILL if needed
5. **Removed**: Delete from `active_processes`

---

## Data Flow Diagram

```
┌─────────────┐
│   Browser   │
│  (Frontend) │
└──────┬──────┘
       │
       │ 1. POST /api/generate
       │    { topic, source_urls, research_enabled }
       │
       ▼
┌─────────────────┐
│  FastAPI Backend│
│   (SSE Server)  │
└──────┬──────────┘
       │
       │ 2. Spawn subprocess
       │    poetry run python -m src.ugly_script
       │
       ▼
┌─────────────────┐
│  Article Script │
│  (Python)       │
└──────┬──────────┘
       │
       │ 3. Write topic → topic.txt
       │    Stdout → Log messages
       │    Write result → output.txt
       │
       ▼
┌─────────────────┐
│  FastAPI Backend│
│  (Read outputs) │
└──────┬──────────┘
       │
       │ 4. SSE Events:
       │    event: message → [INFO] log lines
       │    event: result  → article content
       │    event: close   → done
       │    event: error   → error details
       │
       ▼
┌─────────────┐
│   Browser   │
│ (Update UI) │
└─────────────┘
```

---

## Storage Locations

### Temporary Files (Existing Pattern)

| File | Purpose | Lifecycle | Owner |
|------|---------|-----------|-------|
| `topic.txt` | Input: article topic | Created by backend, read by script, deleted after | Backend |
| `output.txt` | Output: generated article | Created by script, read by backend, deleted after | Script |

**Note**: These files are per-request. In multi-process environment, use temp directories with unique names (e.g., `/tmp/{request_id}/topic.txt`).

### Browser Storage

| Key | Value | Persistence |
|-----|-------|-------------|
| `theme` | `"light"` or `"dark"` | localStorage (permanent) |

### In-Memory (Backend)

| Structure | Purpose | Persistence |
|-----------|---------|-------------|
| `active_processes: dict[str, ProcessTracker]` | Track running generations | Runtime only (cleared on restart) |

---

## Schema Versioning

**Current Version**: `v1`

No breaking changes expected in v1. Future enhancements:
- Add `generation_id` to track history
- Add `user_id` for multi-user support
- Add `created_at` timestamp to requests

Versioning strategy:
- API path: `/api/v1/generate` (when v2 needed)
- Accept header: `Accept: application/vnd.textscript.v1+json`

---

## Validation Summary

| Model | Frontend Validation | Backend Validation |
|-------|---------------------|-------------------|
| GenerationRequest | Non-empty check (UI disabled state) | Pydantic model (length, format, count) |
| LogMessage | N/A (receive-only) | Format validation on stdout parsing |
| GeneratedArticle | Max length warning (50K chars) | Enforce max length, UTF-8 encoding |
| ErrorResponse | Display only | Construct with proper type/message |

---

## Notes

1. **Stateless Design**: No database, no user accounts. Each request is independent.
2. **Idempotency**: Requests are NOT idempotent (each generates a new article).
3. **Concurrency**: Single-session limitation (one generation at a time per browser). Frontend prevents concurrent requests via UI state.
4. **Data Privacy**: No logs persisted. Article content not stored (user downloads manually).
5. **Scalability**: For multi-user, add Redis for process tracking and session storage.
