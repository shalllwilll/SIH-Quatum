"""
backend/app/routers/vehicles.py — Milestone 6.1 & 6.3

CRUD, position polling, and status update endpoints for fleet vehicles.
"""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.db import get_db
from app.models.vehicle import Vehicle, VehicleCreate, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


class VehiclePosition(BaseModel):
    """Real-time vehicle simulated position."""

    vehicle_id: str
    label: str
    lat: float
    lon: float
    heading_deg: float = Field(0.0, description="Direction in degrees (0-360)")
    speed_kmh: float = Field(30.0, description="Current speed in km/h")
    status: str = Field("idle", description="Vehicle operational status")
    driver_id: str | None = None
    current_stop_index: int = 0
    total_stops: int = 0


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


@router.get("/positions", response_model=list[VehiclePosition])
async def get_all_vehicle_positions():
    """
    Bulk vehicle positions endpoint for Admin Fleet Overview map polling (spec §6).
    """
    db = get_db()
    cursor = db["vehicles"].find()
    docs = await cursor.to_list(length=100)

    # Base coordinates in Pune
    base_lat = 18.5204
    base_lon = 73.8567

    positions: list[VehiclePosition] = []
    for idx, doc in enumerate(docs):
        v_id = str(doc["_id"])
        label = doc.get("label", f"Van-{idx+1}")
        status_val = doc.get("status", "idle")
        driver_id = doc.get("driver_id")

        # Slight spatial offset for distinct vehicle markers
        offset_lat = ((idx * 7) % 11) * 0.005 - 0.02
        offset_lon = ((idx * 5) % 13) * 0.005 - 0.02

        positions.append(
            VehiclePosition(
                vehicle_id=v_id,
                label=label,
                lat=round(base_lat + offset_lat, 5),
                lon=round(base_lon + offset_lon, 5),
                heading_deg=float((idx * 45) % 360),
                speed_kmh=28.0 if status_val in ("en_route", "delivering") else 0.0,
                status=status_val,
                driver_id=driver_id,
                current_stop_index=1,
                total_stops=8,
            )
        )

    return positions


@router.post("", response_model=Vehicle, status_code=status.HTTP_201_CREATED)
async def create_vehicle(vehicle_in: VehicleCreate):
    """Register a new vehicle in the fleet."""
    db = get_db()
    doc = vehicle_in.model_dump(exclude_unset=True)
    res = await db["vehicles"].insert_one(doc)
    created_doc = await db["vehicles"].find_one({"_id": res.inserted_id})
    return _doc_to_vehicle(created_doc)


@router.get("/{vehicle_id}/position", response_model=VehiclePosition)
async def get_single_vehicle_position(vehicle_id: str):
    """Fetch live simulated position for a single vehicle."""
    db = get_db()
    try:
        obj_id = ObjectId(vehicle_id)
        doc = await db["vehicles"].find_one({"_id": obj_id})
    except (InvalidId, Exception):
        doc = await db["vehicles"].find_one({"label": vehicle_id})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID or label '{vehicle_id}' not found.",
        )

    v_id = str(doc["_id"])
    label = doc.get("label", "Van-1")
    status_val = doc.get("status", "idle")
    driver_id = doc.get("driver_id")

    return VehiclePosition(
        vehicle_id=v_id,
        label=label,
        lat=18.5204,
        lon=73.8567,
        heading_deg=90.0,
        speed_kmh=25.0 if status_val in ("en_route", "delivering") else 0.0,
        status=status_val,
        driver_id=driver_id,
        current_stop_index=1,
        total_stops=6,
    )


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
