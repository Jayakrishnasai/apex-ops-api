"""
Tests for /health and /ready endpoints.

Checks:
  1. health_returns_200
  2. health_response_schema
  3. health_contains_version
  4. ready_without_db_returns_503   (DB dependency not available in this test)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def bare_client():
    """Client with NO database override — /ready will hit a real DB attempt."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Check 1 ───────────────────────────────────────────────────────────────────


def test_health_returns_200(client):
    """Liveness probe must always return HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


# ── Check 2 ───────────────────────────────────────────────────────────────────


def test_health_response_schema(client):
    """Response must contain status, version, and service fields."""
    body = client.get("/health").json()
    assert "status" in body
    assert "version" in body
    assert "service" in body


# ── Check 3 ───────────────────────────────────────────────────────────────────


def test_health_status_is_healthy(client):
    """The status value must be 'healthy'."""
    body = client.get("/health").json()
    assert body["status"] == "healthy"


# ── Check 4 ───────────────────────────────────────────────────────────────────


def test_health_contains_version(client):
    """Version field must be a non-empty string."""
    body = client.get("/health").json()
    assert isinstance(body["version"], str)
    assert len(body["version"]) > 0


# ── Check 5 ───────────────────────────────────────────────────────────────────


def test_ready_with_db_returns_200(client):
    """
    Readiness probe returns 200 when the DB override (SQLite) is active.
    The dependency override patches check_db_connection via the session.
    """
    # We monkeypatch check_db_connection to return True since our test DB
    # is SQLite and the readiness route calls check_db_connection directly.
    import app.routes.health as health_module

    original = health_module.check_db_connection
    health_module.check_db_connection = lambda: True
    try:
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["database"] == "connected"
    finally:
        health_module.check_db_connection = original


# ── Check 6 ───────────────────────────────────────────────────────────────────


def test_ready_without_db_returns_503(bare_client):
    """
    Readiness probe must return 503 when the database is unreachable.
    Demonstrates CI/CD blocking: a bad DB config must block traffic.
    """
    import app.routes.health as health_module

    original = health_module.check_db_connection
    health_module.check_db_connection = lambda: False
    try:
        response = bare_client.get("/ready")
        assert response.status_code == 503
    finally:
        health_module.check_db_connection = original
