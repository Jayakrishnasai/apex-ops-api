"""
Shared pytest fixtures.

Uses an in-memory SQLite database so tests run without a real PostgreSQL
instance. The database dependency is overridden in every TestClient fixture.
"""

import os

# Set testing environment variables before importing any application modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "testing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# In-memory SQLite — no external services required
SQLITE_URL = "sqlite://"


@pytest.fixture(scope="session")
def db_engine():
    """Create a shared in-memory engine for the entire test session."""
    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Provide a transactional DB session; rolls back after each test."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session):
    """
    Return a FastAPI TestClient with the DB dependency overridden to use
    the in-memory SQLite session.
    """

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()
