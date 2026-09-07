"""
backend/app/routers/driver.py — Milestone 6.3

Driver-specific manifest and isolated vehicle tracking endpoints:
- GET /driver/manifest (itinerary for authenticated driver's vehicle)
- GET /driver/position (position for authenticated driver's vehicle only)
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.middleware import require_driver
from app.db import get_db
from app.simulation.clock import sim_clock
from app.simulation.position_interpolator import interpolate_vehicle_position

router = APIRouter(prefix="/driver", tags=["Driver"])


class ItineraryStop(BaseModel):
    """Single stop in driver manifest."""

    stop_index: int
    parcel_id: str
    address: str
    lat: float
    lon: float
    weight_kg: float
    sla_start_min: int
    sla_deadline_min: int
    scheduled_arrival_min: float
    status: str


class DriverManifestResponse(BaseModel):
    """Driver assigned manifest itinerary payload."""

    driver_id: str
    vehicle_label: str
    session_id: str | None = None
    itinerary: list[ItineraryStop] = Field(default_factory=list)


@router.get("/manifest", response_model=DriverManifestResponse)
async def get_driver_manifest(driver_user: Annotated[dict[str, Any], Depends(require_driver)]):
    """Fetch assigned route manifest for the logged-in driver."""
    driver_id = driver_user.get("sub", driver_user.get("id", "driver1"))
    vehicle_label = driver_user.get("vehicle_label", "Van-1")

    db = get_db()

    # Find active routing session with vehicle assignments
    session = await db["routing_sessions"].find_one(
        {"status": "completed"},
        sort=[("created_at", -1)],
    )

    itinerary: list[ItineraryStop] = []
    session_id: str | None = None

    if session:
        session_id = str(session["_id"])
        assignments = session.get("vehicle_assignments", [])
        for a in assignments:
            if a.get("vehicle_id") == vehicle_label:
                # Build stops
                for idx, arr in enumerate(a.get("stop_arrivals", [])):
                    pid = arr.get("stop_id", f"P-{idx+1}")
                    arr_min = float(arr.get("arrival_time_min", 600.0))
                    itinerary.append(
                        ItineraryStop(
                            stop_index=idx + 1,
                            parcel_id=pid,
                            address=f"Delivery Stop #{idx+1}, Pune",
                            lat=18.5204 + (idx * 0.005),
                            lon=73.8567 + (idx * 0.004),
                            weight_kg=5.0,
                            sla_start_min=540,
                            sla_deadline_min=900,
                            scheduled_arrival_min=round(arr_min, 1),
                            status="pending",
                        )
                    )

    # Fallback default stops if no session active yet
    if not itinerary:
        itinerary = [
            ItineraryStop(
                stop_index=1,
                parcel_id=f"P-{vehicle_label}-01",
                address="FC Road, Deccan Gymkhana, Pune",
                lat=18.5196,
                lon=73.8436,
                weight_kg=4.5,
                sla_start_min=540,
                sla_deadline_min=720,
                scheduled_arrival_min=565.0,
                status="pending",
            )
        ]

    return DriverManifestResponse(
        driver_id=driver_id,
        vehicle_label=vehicle_label,
        session_id=session_id,
        itinerary=itinerary,
    )


@router.get("/position")
async def get_driver_position(driver_user: Annotated[dict[str, Any], Depends(require_driver)]):
    """Fetch current position for the logged-in driver's vehicle only (Milestone 9.1)."""
    driver_id = driver_user.get("sub", driver_user.get("id", "driver1"))
    vehicle_label = driver_user.get("vehicle_label", "Van-1")

    db = get_db()
    veh_doc = await db["vehicles"].find_one({"label": vehicle_label})

    if not veh_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No vehicle found for driver '{driver_id}' ({vehicle_label}).",
        )

    # Fetch active assignment
    session = await db["routing_sessions"].find_one(
        {"status": "completed"},
        sort=[("created_at", -1)],
    )

    assignment = None
    if session:
        for a in session.get("vehicle_assignments", []):
            if a.get("vehicle_id") == vehicle_label:
                assignment = a
                break

    # Warehouse & Stops coords
    wh_doc = await db["warehouses"].find_one()
    wh_coords = (wh_doc.get("lat", 18.5204), wh_doc.get("lon", 73.8567)) if wh_doc else (18.5204, 73.8567)

    parcels_cursor = db["parcels"].find()
    parcels_docs = await parcels_cursor.to_list(length=300)
    stops_coords: dict[str, tuple[float, float]] = {}
    for p in parcels_docs:
        key = str(p.get("_id", p.get("parcel_id", "P-UNKNOWN")))
        stops_coords[key] = (float(p.get("lat", 18.5204)), float(p.get("lon", 73.8567)))
        if "parcel_id" in p:
            stops_coords[str(p["parcel_id"])] = (float(p.get("lat", 18.5204)), float(p.get("lon", 73.8567)))

    current_sim_time = sim_clock.get_current_time_min()

    if assignment:
        interp = interpolate_vehicle_position(
            assignment=assignment,
            stops_coords=stops_coords,
            warehouse_coords=wh_coords,
            current_time_min=current_sim_time,
        )
        return {
            "vehicle_id": str(veh_doc["_id"]),
            "label": vehicle_label,
            "driver_id": driver_id,
            "lat": interp.lat,
            "lon": interp.lon,
            "heading_deg": interp.heading_deg,
            "speed_kmh": interp.speed_kmh,
            "status": interp.status,
            "current_stop_index": interp.current_stop_index,
            "total_stops": interp.total_stops,
        }

    return {
        "vehicle_id": str(veh_doc["_id"]),
        "label": vehicle_label,
        "driver_id": driver_id,
        "lat": wh_coords[0],
        "lon": wh_coords[1],
        "heading_deg": 0.0,
        "speed_kmh": 0.0,
        "status": veh_doc.get("status", "idle"),
        "current_stop_index": 0,
        "total_stops": 0,
    }
