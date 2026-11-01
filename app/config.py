"""
Application configuration loaded exclusively from environment variables.
Never hard-code secrets here — use .env (git-ignored) or a secrets manager.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "Apex Operations API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    # Injected at runtime; never committed to source control.
    database_url: str = "postgresql://apex:changeme@db:5432/apex_db"

    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
