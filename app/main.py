"""
Apex Operations API — application entry point.

Startup sequence:
  1. Structured logging is initialised.
  2. Database tables are created (idempotent via CREATE TABLE IF NOT EXISTS).
  3. Prometheus metrics middleware is attached.
  4. Routers are registered.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from .config import get_settings
from .database import Base, get_engine
from .logger import setup_logging
from .routes import health as health_router
from .routes import items as items_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    # ── Startup ──────────────────────────────────────────────────────────────
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info(
        "Starting Apex Operations API",
        extra={"version": settings.app_version, "env": settings.environment},
    )
    # Create tables if they don't exist (dev convenience; use Alembic in prod)
    Base.metadata.create_all(bind=get_engine())
    logger.info("Database schema ensured")
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    get_engine().dispose()
    logger.info("Application shut down cleanly")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Apex Operations API — Junior DevOps Engineer Assessment",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Prometheus metrics (exposed at /metrics) ──────────────────────────────────
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger = logging.getLogger(__name__)
    logger.error(
        "Unhandled exception",
        extra={"path": request.url.path, "error": str(exc)},
        exc_info=exc,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health_router.router)
app.include_router(items_router.router, prefix="/items", tags=["items"])


@app.get("/", include_in_schema=False)
def root():
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}
