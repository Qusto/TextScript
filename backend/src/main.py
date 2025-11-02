"""
FastAPI backend for TextScript article generation.

AICODE-NOTE: This backend wraps the existing Python article script
with SSE (Server-Sent Events) streaming to provide real-time progress
updates to the web frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
import os

# AICODE-NOTE: Loguru setup for structured logging with colors
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
           "<level>{message}</level>",
    level="INFO",
    colorize=True
)

# AICODE-NOTE: FastAPI app initialization
app = FastAPI(
    title="TextScript API",
    description="SSE streaming API for article generation",
    version="0.1.0"
)

# AICODE-NOTE: CORS middleware to allow requests from Next.js frontend
# Frontend runs on http://localhost:3000 in development
# AICODE-FIX: Added wildcard origin for production deployment flexibility
# AICODE-NOTE: For production, allow any origin (can be restricted by setting CORS_ORIGINS env var)
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
if cors_origins == ["*"]:
    # AICODE-NOTE: Wildcard for development and production flexibility
    # In strict production, set CORS_ORIGINS="http://your-domain.com,http://192.168.0.24:3000"
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # AICODE-NOTE: Allow all HTTP methods for flexibility
    allow_headers=["*"],  # AICODE-NOTE: Allow all headers including custom ones
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - basic API info."""
    logger.info("Root endpoint accessed")
    return {
        "service": "TextScript API",
        "version": "0.1.0",
        "status": "running"
    }


@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup.

    AICODE-NOTE: T086 - Database initialization on application start
    Creates database tables if they don't exist.
    Safe to call multiple times (idempotent).
    """
    from src.db.database import init_db

    logger.info("Application startup: initializing database...")
    init_db()
    logger.success("Application startup complete")


@app.get("/health")
async def health() -> dict[str, str | int]:
    """
    Health check endpoint.

    AICODE-NOTE: T067 - Extended health check with active process count.
    Used by Docker health checks and monitoring systems.
    Returns active_processes count for operational visibility.
    """
    from src.api.generate import process_manager

    logger.debug("Health check accessed")
    return {
        "status": "healthy",
        "active_processes": len(process_manager.active_processes)
    }


# AICODE-NOTE: Import and include routers
from src.api.generate import router as generate_router
from src.api.profiles import router as profiles_router

app.include_router(generate_router, prefix="/api", tags=["generation"])
# AICODE-NOTE: T088 - Include profiles router for style profile management
app.include_router(profiles_router, tags=["profiles"])

if __name__ == "__main__":
    import uvicorn

    # AICODE-NOTE: For development only - production uses docker-compose
    logger.info("Starting FastAPI development server")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # AICODE-NOTE: Auto-reload on code changes
        log_level="info"
    )
