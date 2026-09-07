"""
backend/app/routers/warehouses.py — Milestone 6.1

CRUD endpoints for warehouse distribution hubs.
"""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, status

from app.db import get_db
from app.models.warehouse import Warehouse, WarehouseCreate

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


def _doc_to_warehouse(doc: dict[str, Any]) -> Warehouse:
    """Convert a MongoDB document into a Pydantic Warehouse model."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return Warehouse.model_validate(doc)


@router.get("", response_model=list[Warehouse])
async def list_warehouses():
    """List all registered warehouse distribution hubs."""
    db = get_db()
    cursor = db["warehouses"].find()
    docs = await cursor.to_list(length=100)
    return [_doc_to_warehouse(d) for d in docs]


@router.post("", response_model=Warehouse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(warehouse_in: WarehouseCreate):
    """Create a new warehouse distribution hub."""
    db = get_db()
    doc = warehouse_in.model_dump(exclude_unset=True)
    res = await db["warehouses"].insert_one(doc)
    created_doc = await db["warehouses"].find_one({"_id": res.inserted_id})
    return _doc_to_warehouse(created_doc)


@router.get("/{warehouse_id}", response_model=Warehouse)
async def get_warehouse(warehouse_id: str):
    """Retrieve a single warehouse by MongoDB ObjectId."""
    try:
        obj_id = ObjectId(warehouse_id)
    except InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse with ID '{warehouse_id}' not found.",
        ) from exc

    db = get_db()
    doc = await db["warehouses"].find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse with ID '{warehouse_id}' not found.",
        )

    return _doc_to_warehouse(doc)
