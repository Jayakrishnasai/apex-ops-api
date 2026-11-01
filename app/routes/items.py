"""
CRUD routes for the /items resource.

All write operations are logged for audit purposes using structured JSON logs.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item
from app.schemas import (
    ItemCreate,
    ItemListResponse,
    ItemResponse,
    ItemUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ItemResponse, status_code=201, summary="Create an item")
def create_item(payload: ItemCreate, db: Session = Depends(get_db)) -> Item:
    """Create and persist a new operational item."""
    item = Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    logger.info("Item created", extra={"item_id": item.id, "item_name": item.name})
    return item


@router.get("/", response_model=ItemListResponse, summary="List items")
def list_items(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
) -> ItemListResponse:
    """Return a paginated list of items, optionally filtered by status."""
    query = select(Item)
    count_query = select(func.count()).select_from(Item)

    if status:
        query = query.where(Item.status == status)
        count_query = count_query.where(Item.status == status)

    total = db.execute(count_query).scalar_one()
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()

    return ItemListResponse(items=list(items), total=total, page=page, page_size=page_size)


@router.get("/{item_id}", response_model=ItemResponse, summary="Get an item")
def get_item(item_id: int, db: Session = Depends(get_db)) -> Item:
    """Retrieve a single item by its ID. Returns 404 if not found."""
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item


@router.put("/{item_id}", response_model=ItemResponse, summary="Update an item")
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)) -> Item:
    """Update one or more fields of an existing item (PATCH semantics via PUT)."""
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    logger.info("Item updated", extra={"item_id": item.id, "fields": list(update_data)})
    return item


@router.delete("/{item_id}", status_code=204, summary="Delete an item")
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    """Permanently remove an item. Returns 204 No Content on success."""
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    db.delete(item)
    db.commit()
    logger.info("Item deleted", extra={"item_id": item_id})
