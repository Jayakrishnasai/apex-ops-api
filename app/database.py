"""
Database engine and session factory.

The engine is created lazily via get_engine() so that:
  - Tests can set DATABASE_URL to a SQLite URL before any import triggers
    a PostgreSQL connection (which would fail without pg_config on Windows).
  - pool_pre_ping=True ensures stale connections are detected and recycled
    automatically in long-running containerised deployments.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_engine = None
_SessionLocal = None


def get_engine():
    """Return (and lazily initialise) the shared SQLAlchemy engine."""
    global _engine
    if _engine is None:
        from .config import get_settings

        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args=connect_args,
            echo=settings.debug,
        )
    return _engine


def get_session_local():
    """Return (and lazily initialise) the shared sessionmaker."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def __getattr__(name: str):
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def get_db():
    """FastAPI dependency that yields a database session and ensures cleanup."""
    SessionLocal = get_session_local()
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
