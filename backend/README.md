# TextScript Backend

FastAPI backend for wrapping the existing Python article generation script with SSE (Server-Sent Events) streaming.

## Setup

This backend is part of the `002-web-frontend-docker` feature implementation.

### Prerequisites

- Python 3.11+
- Poetry 1.7+

### Installation

```bash
cd backend
poetry install
```

## Development

### Run the server

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### Run tests

```bash
poetry run pytest -v
```

### Run tests with coverage

```bash
poetry run pytest --cov=src --cov-report=term-missing
```

## API Endpoints

### GET /

Root endpoint - returns API information.

### GET /health

Health check endpoint for Docker and monitoring systems.

**Response:**
```json
{
  "status": "healthy"
}
```

### POST /api/generate (Coming in Phase 2)

SSE streaming endpoint for article generation.

## Project Structure

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── api/                 # API route handlers
│   │   ├── __init__.py
│   │   └── generate.py      # SSE streaming endpoint (TODO)
│   └── services/            # Business logic
│       ├── __init__.py
│       └── process_manager.py  # Subprocess lifecycle management (TODO)
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Basic FastAPI tests
├── pyproject.toml           # Poetry configuration
└── README.md                # This file
```

## Key Technologies

- **FastAPI** - Modern async web framework with automatic OpenAPI docs
- **Uvicorn** - ASGI server for long-running SSE connections
- **Loguru** - Structured logging with colors
- **Pydantic** - Request/response validation
- **pytest** - Testing framework with async support

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000` (development frontend)
- `http://frontend:3000` (Docker Compose frontend)

## Next Steps

See `/Users/teterinsa/Projects/TextScript/specs/002-web-frontend-docker/tasks.md` for implementation tasks.

**Phase 1 (Setup): ✅ Complete**
- T009-T012: Backend directory structure and initialization

**Phase 2 (Foundational): 🔜 Next**
- T013-T020: ProcessManager and SSE streaming implementation
