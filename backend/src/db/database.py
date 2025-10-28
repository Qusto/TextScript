"""
SQLite database initialization and session management.

AICODE-NOTE: T086 - Database setup for style profile storage (FR-028)
Uses SQLAlchemy ORM with SQLite for single-user profile management.
Database location: backend/profiles.db (not in src/ to avoid Docker volume conflicts)

TODO: T093 - Migrate to PostgreSQL for multi-user support in future versions
When scaling to multiple users, replace SQLite with PostgreSQL:
- Add asyncpg driver
- Update connection string
- Add connection pooling
- Implement proper transaction management
- Add database migrations with Alembic
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

# AICODE-NOTE: T086 - Database file location (FR-028)
# Store profiles.db in backend/ directory (not in src/ to avoid Docker volume overwrites)
DATABASE_PATH = Path(__file__).parent.parent.parent / "profiles.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

logger.info(f"Database URL: {DATABASE_URL}")

# AICODE-NOTE: T086 - SQLAlchemy engine configuration
# check_same_thread=False: Required for SQLite with FastAPI (async context)
# connect_args only applies to SQLite, safe to use
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # Set to True for SQL query logging during development
)

# AICODE-NOTE: T086 - Session factory for database connections
# autocommit=False: Explicit transaction control
# autoflush=False: Manual flush control for better performance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# AICODE-NOTE: T086 - Declarative base for ORM models
# All database models will inherit from this base
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI to get database session.

    AICODE-NOTE: T086 - Database session management pattern
    Yields a database session that automatically closes after use.
    Use this as a FastAPI dependency: Depends(get_db)

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/api/profiles")
        def get_profiles(db: Session = Depends(get_db)):
            return db.query(StyleProfileDB).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.

    AICODE-NOTE: T086 - Database initialization
    Creates all tables defined in models.py if they don't exist.
    Called on application startup in main.py.

    Safe to call multiple times - only creates missing tables.
    """
    logger.info("Initializing database...")

    # AICODE-NOTE: Import models to register them with Base
    # This must happen before create_all() is called
    from src.db.models import StyleProfileDB  # noqa: F401

    # AICODE-NOTE: Create all tables defined in Base metadata
    Base.metadata.create_all(bind=engine)

    logger.success(f"Database initialized at {DATABASE_PATH}")

    # AICODE-NOTE: Log database file size for monitoring
    if DATABASE_PATH.exists():
        size_kb = DATABASE_PATH.stat().st_size / 1024
        logger.info(f"Database size: {size_kb:.2f} KB")
