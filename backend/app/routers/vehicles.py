"""
backend/app/routers/vehicles.py — Milestone 6.1 & 9.1

CRUD, live accelerated-clock position simulation, and status update endpoints for fleet vehicles.
"""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.db import get_db
from app.models.vehicle import Vehicle, VehicleCreate, VehicleUpdate
from app.simulation.clock import sim_clock
from app.simulation.position_interpolator import interpolate_vehicle_position

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


async def _get_stops_and_warehouse_lookups(db: Any) -> tuple[dict[str, tuple[float, float]], tuple[float, float]]:
    """Fetch stops coordinates and primary warehouse coordinates."""
    # Warehouse
    wh_doc = await db["warehouses"].find_one()
    wh_coords = (wh_doc.get("lat", 18.5204), wh_doc.get("lon", 73.8567)) if wh_doc else (18.5204, 73.8567)

    # Parcels
    parcels_cursor = db["parcels"].find()
    parcels_docs = await parcels_cursor.to_list(length=300)
    stops_coords: dict[str, tuple[float, float]] = {}
    for p in parcels_docs:
        key = str(p.get("_id", p.get("parcel_id", "P-UNKNOWN")))
        stops_coords[key] = (float(p.get("lat", 18.5204)), float(p.get("lon", 73.8567)))
        if "parcel_id" in p:
            stops_coords[str(p["parcel_id"])] = (float(p.get("lat", 18.5204)), float(p.get("lon", 73.8567)))

    return stops_coords, wh_coords


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
    Bulk vehicle positions endpoint for Admin Fleet Overview map polling (spec §6, Milestone 9.1).
    Uses the accelerated-clock position interpolator across active route assignments.
    """
    db = get_db()
    cursor = db["vehicles"].find()
    veh_docs = await cursor.to_list(length=100)

    # Fetch latest session with vehicle assignments
    session = await db["routing_sessions"].find_one(
        {"status": "completed"},
        sort=[("created_at", -1)],
    )

    assignment_map: dict[str, dict[str, Any]] = {}
    if session:
        for a in session.get("vehicle_assignments", []):
            v_key = a.get("vehicle_id")
            if v_key:
                assignment_map[v_key] = a

    stops_coords, wh_coords = await _get_stops_and_warehouse_lookups(db)
    current_sim_time = sim_clock.get_current_time_min()

    positions: list[VehiclePosition] = []
    for idx, doc in enumerate(veh_docs):
        v_id = str(doc["_id"])
        label = doc.get("label", f"Van-{idx+1}")
        driver_id = doc.get("driver_id")
        db_status = doc.get("status", "idle")

        assignment = assignment_map.get(label) or assignment_map.get(v_id)

        if assignment:
            # Interpolate position along real assigned route legs
            interp = interpolate_vehicle_position(
                assignment=assignment,
                stops_coords=stops_coords,
                warehouse_coords=wh_coords,
                current_time_min=current_sim_time,
            )
            positions.append(
                VehiclePosition(
                    vehicle_id=v_id,
                    label=label,
                    lat=interp.lat,
                    lon=interp.lon,
                    heading_deg=interp.heading_deg,
                    speed_kmh=interp.speed_kmh,
                    status=interp.status,
                    driver_id=driver_id,
                    current_stop_index=interp.current_stop_index,
                    total_stops=interp.total_stops,
                )
            )
        else:
            # Fallback staged coordinate for unassigned vehicles
            offset_lat = ((idx * 7) % 11) * 0.005 - 0.02
            offset_lon = ((idx * 5) % 13) * 0.005 - 0.02
            positions.append(
                VehiclePosition(
                    vehicle_id=v_id,
                    label=label,
                    lat=round(wh_coords[0] + offset_lat, 5),
                    lon=round(wh_coords[1] + offset_lon, 5),
                    heading_deg=float((idx * 45) % 360),
                    speed_kmh=28.0 if db_status in ("en_route", "delivering") else 0.0,
                    status=db_status,
                    driver_id=driver_id,
                    current_stop_index=0,
                    total_stops=0,
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
    """Fetch live simulated position for a single vehicle (Milestone 9.1)."""
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
    driver_id = doc.get("driver_id")
    db_status = doc.get("status", "idle")

    # Fetch assignment
    session = await db["routing_sessions"].find_one(
        {"status": "completed"},
        sort=[("created_at", -1)],
    )

    assignment = None
    if session:
        for a in session.get("vehicle_assignments", []):
            if a.get("vehicle_id") in (label, v_id):
                assignment = a
                break

    stops_coords, wh_coords = await _get_stops_and_warehouse_lookups(db)
    current_sim_time = sim_clock.get_current_time_min()

    if assignment:
        interp = interpolate_vehicle_position(
            assignment=assignment,
            stops_coords=stops_coords,
            warehouse_coords=wh_coords,
            current_time_min=current_sim_time,
        )
        return VehiclePosition(
            vehicle_id=v_id,
            label=label,
            lat=interp.lat,
            lon=interp.lon,
            heading_deg=interp.heading_deg,
            speed_kmh=interp.speed_kmh,
            status=interp.status,
            driver_id=driver_id,
            current_stop_index=interp.current_stop_index,
            total_stops=interp.total_stops,
        )

    return VehiclePosition(
        vehicle_id=v_id,
        label=label,
        lat=wh_coords[0],
        lon=wh_coords[1],
        heading_deg=0.0,
        speed_kmh=25.0 if db_status in ("en_route", "delivering") else 0.0,
        status=db_status,
        driver_id=driver_id,
        current_stop_index=0,
        total_stops=0,
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
