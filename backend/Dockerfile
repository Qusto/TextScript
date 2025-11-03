# AICODE-NOTE: T057 - Multi-stage Dockerfile for FastAPI backend
# Targets python:3.11-slim for balance between size and compatibility
# Two stages: deps (install dependencies), runtime (production)

# Stage 1: Install dependencies with Poetry
# AICODE-NOTE: Separate stage for building dependencies with Poetry
FROM python:3.11-slim AS deps
WORKDIR /app

# AICODE-NOTE: Install Poetry for dependency management
# Pin version for reproducible builds (1.8+ supports package-mode)
RUN pip install --no-cache-dir poetry==1.8.5

# AICODE-NOTE: Configure Poetry to not create virtual env (already in container)
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# AICODE-NOTE: Copy only dependency files for better caching
COPY pyproject.toml poetry.lock ./
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Stage 2: Runtime
# AICODE-NOTE: Final minimal image with Python runtime
FROM python:3.11-slim AS runtime
WORKDIR /app

# AICODE-NOTE: Install runtime system dependencies
# - curl: for health checks
# - ca-certificates: for HTTPS requests
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# AICODE-NOTE: Run as non-root user for security
RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 --gid 1001 appuser

# AICODE-NOTE: Copy installed dependencies from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# AICODE-NOTE: Copy application source code
COPY --chown=appuser:appuser ./src ./src
COPY --chown=appuser:appuser ./pyproject.toml ./

# AICODE-NOTE: Create directory for output files and database
RUN mkdir -p /app/output && chown appuser:appuser /app/output
RUN mkdir -p /app && chown appuser:appuser /app

USER appuser

# AICODE-NOTE: Expose port 8000 (FastAPI default)
EXPOSE 8000

# AICODE-NOTE: Environment variables for production
# Add /app to PYTHONPATH so Python can find src module
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

# AICODE-NOTE: Health check to verify service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# AICODE-NOTE: Start uvicorn server
# - host 0.0.0.0: listen on all interfaces (required for Docker)
# - port 8000: FastAPI default
# - log-level info: standard production logging
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
