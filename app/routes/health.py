"""
Health and readiness endpoints.

/health  → liveness probe  (always fast; no external dependencies)
/ready   → readiness probe (checks database reachability)

These are called by Docker HEALTHCHECK, Docker Compose condition checks,
and Kubernetes liveness/readiness probes.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.database import check_db_connection
from app.schemas import HealthResponse, ReadinessResponse

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    tags=["health"],
)
def health_check() -> HealthResponse:
    """
    Returns 200 when the application process is running.
    Does NOT check external dependencies — use /ready for that.
    """
    logger.debug("Liveness probe called")
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        service=settings.app_name,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    tags=["health"],
)
def readiness_check() -> ReadinessResponse:
    """
    Returns 200 when the application is ready to serve traffic.
    Verifies database connectivity — returns 503 if the DB is unreachable.
    """
    logger.debug("Readiness probe called")
    if not check_db_connection():
        logger.error("Readiness check failed: database unreachable")
        raise HTTPException(
            status_code=503,
            detail="Service not ready: database connection failed",
        )
    return ReadinessResponse(status="ready", database="connected")
