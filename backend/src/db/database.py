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


def _migrate_add_name_column():
    """
    Migration: Add 'name' column to style_profiles table.

    AICODE-NOTE: T121 - Database migration for profile name field.
    Checks if 'name' column exists, adds it if missing, and populates
    existing records with generated names.

    Migration steps:
    1. Check column existence via PRAGMA table_info
    2. Add column with ALTER TABLE if missing (default 'Профиль')
    3. Update existing records with generated names from source URLs

    Safe to run multiple times - checks for column existence first.
    """
    from sqlalchemy import text
    import json

    logger.info("Running migration: add 'name' column to style_profiles")

    # AICODE-NOTE: Create raw connection for SQL queries
    # Using text() for SQLAlchemy 2.0 compatibility
    with engine.connect() as conn:
        # AICODE-NOTE: Check if 'name' column already exists
        # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
        result = conn.execute(text("PRAGMA table_info(style_profiles)"))
        columns = [row[1] for row in result.fetchall()]

        if "name" in columns:
            logger.info("Column 'name' already exists, skipping migration")
            return

        logger.info("Column 'name' not found, adding to table...")

        # AICODE-NOTE: T121 - Add 'name' column with default value
        # Using VARCHAR(100) to match SQLAlchemy model definition
        conn.execute(
            text("ALTER TABLE style_profiles ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT 'Профиль'")
        )
        conn.commit()

        logger.success("Column 'name' added successfully")

        # AICODE-NOTE: T121 - Update existing records with generated names
        # Import generate_profile_name_from_url for URL-based name generation
        from src.api.profiles import generate_profile_name_from_url

        # Fetch all existing profiles
        result = conn.execute(text("SELECT id, source_urls FROM style_profiles"))
        profiles = result.fetchall()

        if not profiles:
            logger.info("No existing profiles to update")
            return

        logger.info(f"Updating {len(profiles)} existing profiles with generated names...")

        # AICODE-NOTE: Update each profile with generated name
        for profile_id, source_urls_json in profiles:
            try:
                # Parse JSON source_urls
                source_urls = json.loads(source_urls_json)

                # Generate profile name from first URL
                if source_urls and isinstance(source_urls, list):
                    profile_name = generate_profile_name_from_url(source_urls[0])
                else:
                    profile_name = "Профиль"

                # Update record (using :param syntax for SQLAlchemy 2.0)
                conn.execute(
                    text("UPDATE style_profiles SET name = :name WHERE id = :id"),
                    {"name": profile_name, "id": profile_id}
                )

                logger.debug(f"Updated profile {profile_id} with name: {profile_name}")

            except Exception as e:
                # AICODE-NOTE: Fallback to default name on error
                logger.warning(f"Failed to generate name for profile {profile_id}: {e}")
                conn.execute(
                    text("UPDATE style_profiles SET name = :name WHERE id = :id"),
                    {"name": "Профиль", "id": profile_id}
                )

        conn.commit()
        logger.success(f"Updated {len(profiles)} profiles with generated names")


def _migrate_add_source_type_column():
    """
    Migration: Add 'source_type' column to style_profiles table.

    AICODE-NOTE: T193 - Database migration for Phase 13 text-based profile creation.
    Adds source_type column to distinguish between URL-based and text-based profiles.

    Migration steps:
    1. Check column existence via PRAGMA table_info
    2. Add column with ALTER TABLE if missing (default 'urls')
    3. Create index for query performance

    Safe to run multiple times - checks for column existence first.
    All existing profiles default to 'urls' for backward compatibility.
    """
    from sqlalchemy import text

    logger.info("Running migration: add 'source_type' column to style_profiles")

    # AICODE-NOTE: Create raw connection for SQL queries
    with engine.connect() as conn:
        # AICODE-NOTE: Check if 'source_type' column already exists
        result = conn.execute(text("PRAGMA table_info(style_profiles)"))
        columns = [row[1] for row in result.fetchall()]

        if "source_type" in columns:
            logger.info("Column 'source_type' already exists, skipping migration")
            return

        logger.info("Column 'source_type' not found, adding to table...")

        # AICODE-NOTE: T193 - Add 'source_type' column with default 'urls'
        # VARCHAR(10) is sufficient for 'urls' and 'text' values
        # Default 'urls' ensures backward compatibility with existing profiles
        conn.execute(
            text("ALTER TABLE style_profiles ADD COLUMN source_type VARCHAR(10) NOT NULL DEFAULT 'urls'")
        )
        conn.commit()

        logger.success("Column 'source_type' added successfully")

        # AICODE-NOTE: T193 - Create index for query performance
        # Index name format: ix_{table}_{column}
        try:
            conn.execute(
                text("CREATE INDEX ix_style_profiles_source_type ON style_profiles(source_type)")
            )
            conn.commit()
            logger.success("Index 'ix_style_profiles_source_type' created successfully")
        except Exception as e:
            # AICODE-NOTE: Index might already exist (safe to ignore)
            logger.debug(f"Index creation skipped (may already exist): {e}")


def init_db():
    """
    Initialize database tables.

    AICODE-NOTE: T086 - Database initialization
    AICODE-NOTE: T121 - Added migration call for 'name' column
    AICODE-NOTE: T193 - Added migration call for 'source_type' column (Phase 13)
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

    # AICODE-NOTE: T121 - Run migration to add 'name' column to existing databases
    _migrate_add_name_column()

    # AICODE-NOTE: T193 - Run migration to add 'source_type' column (Phase 13)
    _migrate_add_source_type_column()

    # AICODE-NOTE: Log database file size for monitoring
    if DATABASE_PATH.exists():
        size_kb = DATABASE_PATH.stat().st_size / 1024
        logger.info(f"Database size: {size_kb:.2f} KB")
