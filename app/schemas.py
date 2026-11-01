"""Pydantic schemas for request validation and response serialisation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ── Request schemas ────────────────────────────────────────────────────────────


class ItemCreate(BaseModel):
    """Payload required to create a new item."""

    name: str = Field(..., min_length=1, max_length=255, examples=["Deploy pipeline"])
    description: str | None = Field(None, max_length=2000, examples=["Set up CD pipeline"])
    status: Literal["active", "inactive", "pending"] = Field("active")


class ItemUpdate(BaseModel):
    """All fields optional — only provided fields are updated (PATCH semantics)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: Literal["active", "inactive", "pending"] | None = None


# ── Response schemas ───────────────────────────────────────────────────────────


class ItemResponse(BaseModel):
    """Full item representation returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ItemListResponse(BaseModel):
    """Paginated list of items."""

    items: list[ItemResponse]
    total: int
    page: int
    page_size: int


# ── Health schemas ─────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
