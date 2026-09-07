"""
backend/app/routers/parcels.py — Milestone 6.1

CRUD and paginated listing endpoints for delivery parcels.
"""

from __future__ import annotations

import math
from typing import Annotated, Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.db import get_db
from app.models.parcel import Parcel, ParcelCreate, ParcelStatus

router = APIRouter(prefix="/parcels", tags=["Parcels"])


class PaginatedParcels(BaseModel):
    """Paginated parcel response payload."""

    items: list[Parcel]
    total: int = Field(..., ge=0, description="Total number of matching parcels")
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=1, description="Total number of pages")


def _doc_to_parcel(doc: dict[str, Any]) -> Parcel:
    """Convert a MongoDB document into a Pydantic Parcel model."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return Parcel.model_validate(doc)


@router.get("", response_model=PaginatedParcels)
async def list_parcels(
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    limit: Annotated[int, Query(ge=1, le=200, description="Items per page")] = 20,
    status_filter: Annotated[
        ParcelStatus | None,
        Query(alias="status", description="Filter by parcel status"),
    ] = None,
):
    """List delivery parcels with pagination and optional status filter."""
    db = get_db()
    query: dict[str, Any] = {}
    if status_filter is not None:
        query["status"] = status_filter.value

    total = await db["parcels"].count_documents(query)
    skip = (page - 1) * limit

    cursor = db["parcels"].find(query).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    pages = max(1, math.ceil(total / limit)) if total > 0 else 1

    return PaginatedParcels(
        items=[_doc_to_parcel(d) for d in docs],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.post("", response_model=Parcel, status_code=status.HTTP_201_CREATED)
async def create_parcel(parcel_in: ParcelCreate):
    """Create a new delivery parcel."""
    db = get_db()
    doc = parcel_in.model_dump(exclude_unset=True)
    res = await db["parcels"].insert_one(doc)
    created_doc = await db["parcels"].find_one({"_id": res.inserted_id})
    return _doc_to_parcel(created_doc)


@router.get("/{parcel_id}", response_model=Parcel)
async def get_parcel(parcel_id: str):
    """Retrieve a single parcel by MongoDB ObjectId."""
    try:
        obj_id = ObjectId(parcel_id)
    except InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID '{parcel_id}' not found.",
        ) from exc

    db = get_db()
    doc = await db["parcels"].find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID '{parcel_id}' not found.",
        )

    return _doc_to_parcel(doc)
