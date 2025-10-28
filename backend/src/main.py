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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Development frontend
        "http://frontend:3000",   # Docker Compose frontend
    ],
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


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Health check endpoint.

    AICODE-NOTE: Used by Docker health checks and monitoring systems.
    Will be extended to include active process count in later phases.
    """
    logger.debug("Health check accessed")
    return {
        "status": "healthy"
    }


# AICODE-TODO: Import and include generate router when implemented
# from src.api.generate import router as generate_router
# app.include_router(generate_router, prefix="/api", tags=["generation"])

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
