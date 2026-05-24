"""
GrokDent FL - Database Configuration
SQLAlchemy engine, session factory, and declarative Base.
Supports SQLite for development and PostgreSQL for production.
"""

import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine setup — SQLite needs check_same_thread=False for FastAPI
# ---------------------------------------------------------------------------
connect_args = {}
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
is_postgres = settings.DATABASE_URL.startswith("postgresql")

if is_sqlite:
    connect_args["check_same_thread"] = False
    if os.environ.get("ENVIRONMENT", "").lower() == "production":
        logger.warning(
            "SQLite detected in production environment! "
            "Set DATABASE_URL to PostgreSQL for production use."
        )

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# WAL mode for SQLite
if is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
