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
        {"status": {"$in": ["assigned", "completed"]}},
        sort=[("created_at", -1), ("_id", -1)],
    )

    itinerary: list[ItineraryStop] = []
    session_id: str | None = None

    # Load parcels lookup for rich address and coordinate display
    parcels_cursor = db["parcels"].find()
    parcels_docs = await parcels_cursor.to_list(length=500)
    parcels_by_id: dict[str, dict[str, Any]] = {}
    for p in parcels_docs:
        parcels_by_id[str(p["_id"])] = p
        if p.get("tracking_number"):
            parcels_by_id[str(p["tracking_number"])] = p
        if p.get("parcel_id"):
            parcels_by_id[str(p["parcel_id"])] = p

    events = []
    delivered_stop_ids = set()
    if session:
        session_id = str(session["_id"])
        # Load logged delivery events for this vehicle in the current active session
        events_cursor = db["delivery_events"].find({
            "routing_session_id": {"$in": [session_id, "SESSION-ACTIVE"]},
            "vehicle_id": vehicle_label,
        }).sort("recorded_at_wall", 1)
        events = await events_cursor.to_list(length=200)

        assignments = session.get("vehicle_assignments", [])
        v_target = vehicle_label.strip().lower()
        matched_assignment = None
        for a in assignments:
            v_cand = str(a.get("vehicle_id", "")).strip().lower()
            if v_cand == v_target or v_cand.replace("-", "") == v_target.replace("-", ""):
                matched_assignment = a
                break

        # 1. First include completed/failed stops from logged events for this session/vehicle
        latest_event_by_parcel: dict[str, dict[str, Any]] = {}
        for ev in events:
            pid_key = str(ev.get("parcel_id"))
            latest_event_by_parcel[pid_key] = ev

        for pid, ev in latest_event_by_parcel.items():
            delivered_stop_ids.add(pid)
            p_doc = parcels_by_id.get(pid)

            addr = (p_doc.get("address") if p_doc else None) or f"Delivery Stop #{len(itinerary)+1}, Pune"
            lat = float(p_doc.get("lat")) if p_doc and "lat" in p_doc else (18.5204 + (len(itinerary) * 0.005))
            lon = float(p_doc.get("lon")) if p_doc and "lon" in p_doc else (73.8567 + (len(itinerary) * 0.004))
            weight = float(p_doc.get("weight_kg", 5.0)) if p_doc else 5.0
            sla_start = int(p_doc.get("sla_start_min", 540)) if p_doc else 540
            sla_end = int(p_doc.get("sla_deadline_min", 900)) if p_doc else 900

            itinerary.append(
                ItineraryStop(
                    stop_index=len(itinerary) + 1,
                    parcel_id=pid,
                    address=addr,
                    lat=round(lat, 6),
                    lon=round(lon, 6),
                    weight_kg=round(weight, 1),
                    sla_start_min=sla_start,
                    sla_deadline_min=sla_end,
                    scheduled_arrival_min=float(ev.get("recorded_at_min", 600.0)),
                    status=ev.get("status", "delivered"),
                )
            )

        # 2. Append remaining active stops from the latest assignment
        if matched_assignment:
            for arr in matched_assignment.get("stop_arrivals", []):
                pid = str(arr.get("stop_id", f"P-{len(itinerary)+1}"))
                if pid in delivered_stop_ids:
                    continue
                arr_min = float(arr.get("arrival_time_min", 600.0))
                p_doc = parcels_by_id.get(pid)

                addr = (p_doc.get("address") if p_doc else None) or f"Delivery Stop #{len(itinerary)+1}, Pune"
                lat = float(p_doc.get("lat")) if p_doc and "lat" in p_doc else (18.5204 + (len(itinerary) * 0.005))
                lon = float(p_doc.get("lon")) if p_doc and "lon" in p_doc else (73.8567 + (len(itinerary) * 0.004))
                weight = float(p_doc.get("weight_kg", 5.0)) if p_doc else 5.0
                sla_start = int(p_doc.get("sla_start_min", 540)) if p_doc else 540
                sla_end = int(p_doc.get("sla_deadline_min", 900)) if p_doc else 900

                itinerary.append(
                    ItineraryStop(
                        stop_index=len(itinerary) + 1,
                        parcel_id=pid,
                        address=addr,
                        lat=round(lat, 6),
                        lon=round(lon, 6),
                        weight_kg=round(weight, 1),
                        sla_start_min=sla_start,
                        sla_deadline_min=sla_end,
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
        veh_doc = await db["vehicles"].find_one({"label": {"$regex": f"^{vehicle_label}$", "$options": "i"}})

    if not veh_doc:
        veh_doc = {"_id": "simulated_veh", "label": vehicle_label, "driver_id": driver_id}

    # Fetch active assignment
    session = await db["routing_sessions"].find_one(
        {"status": {"$in": ["assigned", "completed"]}},
        sort=[("created_at", -1), ("_id", -1)],
    )

    assignment = None
    if session:
        v_target = vehicle_label.strip().lower()
        for a in session.get("vehicle_assignments", []):
            v_cand = str(a.get("vehicle_id", "")).strip().lower()
            if v_cand == v_target or v_cand.replace("-", "") == v_target.replace("-", ""):
                assignment = a
                break

    # Warehouse & Stops coords
    wh_doc = await db["warehouses"].find_one()
    wh_coords = (wh_doc.get("lat", 18.5204), wh_doc.get("lon", 73.8567)) if wh_doc else (18.5204, 73.8567)

    parcels_cursor = db["parcels"].find()
    parcels_docs = await parcels_cursor.to_list(length=500)
    stops_coords: dict[str, tuple[float, float]] = {}
    for p in parcels_docs:
        lat_val = float(p.get("lat", 18.5204))
        lon_val = float(p.get("lon", 73.8567))
        stops_coords[str(p.get("_id"))] = (lat_val, lon_val)
        if p.get("parcel_id"):
            stops_coords[str(p["parcel_id"])] = (lat_val, lon_val)
        if p.get("tracking_number"):
            stops_coords[str(p["tracking_number"])] = (lat_val, lon_val)

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
