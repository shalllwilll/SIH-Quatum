"""
backend/app/routers/vehicles.py — Milestone 6.1

CRUD and status update endpoints for fleet vehicles.
"""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, status

from app.db import get_db
from app.models.vehicle import Vehicle, VehicleCreate, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


def _doc_to_vehicle(doc: dict[str, Any]) -> Vehicle:
    """Convert a MongoDB document into a Pydantic Vehicle model."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return Vehicle.model_validate(doc)


@router.get("", response_model=list[Vehicle])
async def list_vehicles():
    """List all fleet vehicles."""
    db = get_db()
    cursor = db["vehicles"].find()
    docs = await cursor.to_list(length=200)
    return [_doc_to_vehicle(d) for d in docs]


@router.post("", response_model=Vehicle, status_code=status.HTTP_201_CREATED)
async def create_vehicle(vehicle_in: VehicleCreate):
    """Register a new vehicle in the fleet."""
    db = get_db()
    doc = vehicle_in.model_dump(exclude_unset=True)
    res = await db["vehicles"].insert_one(doc)
    created_doc = await db["vehicles"].find_one({"_id": res.inserted_id})
    return _doc_to_vehicle(created_doc)


@router.get("/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: str):
    """Retrieve a single vehicle by MongoDB ObjectId."""
    try:
        obj_id = ObjectId(vehicle_id)
    except InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID '{vehicle_id}' not found.",
        ) from exc

    db = get_db()
    doc = await db["vehicles"].find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID '{vehicle_id}' not found.",
        )

    return _doc_to_vehicle(doc)


@router.patch("/{vehicle_id}", response_model=Vehicle)
async def update_vehicle(vehicle_id: str, vehicle_update: VehicleUpdate):
    """Partially update vehicle status, driver assignment, or location."""
    try:
        obj_id = ObjectId(vehicle_id)
    except InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID '{vehicle_id}' not found.",
        ) from exc

    update_data = vehicle_update.model_dump(exclude_unset=True)
    if not update_data:
        return await get_vehicle(vehicle_id)

    db = get_db()
    result = await db["vehicles"].update_one(
        {"_id": obj_id},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID '{vehicle_id}' not found.",
        )

    updated_doc = await db["vehicles"].find_one({"_id": obj_id})
    return _doc_to_vehicle(updated_doc)
