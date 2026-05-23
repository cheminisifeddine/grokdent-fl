"""
GrokDent FL - Database Configuration
SQLAlchemy engine, session factory, and declarative Base.
Supports SQLite for development and PostgreSQL for production.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings


# ---------------------------------------------------------------------------
# Engine setup — SQLite needs check_same_thread=False for FastAPI
# ---------------------------------------------------------------------------
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Enable WAL mode for SQLite for better concurrent read performance
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ---------------------------------------------------------------------------
# Dependency — yields a DB session per request, auto-closes
# ---------------------------------------------------------------------------
def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
