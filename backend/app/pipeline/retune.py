"""
backend/app/pipeline/retune.py — Milestone 9.2

Tier 1: "Delivered" Event Re-Tune (Spec §3d, §9).
When a parcel is marked delivered, re-runs ONLY QPSO on that vehicle's remaining stops
to re-optimize arrival times and dwell windows without any combinatorial QGA overhead.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from bson import ObjectId

from app.db import get_db
from app.qpso.run_qpso import run_qpso

log = logging.getLogger(__name__)


async def retune_on_delivered(
    session_id: str | ObjectId,
    vehicle_id: str,
    delivered_stop_id: str,
    current_time_min: float,
    db: Any = None,
) -> dict[str, Any]:
    """
    Execute cheap Tier 1 QPSO re-tuning on a vehicle's remaining stops after a delivery.

    Args:
        session_id: ID of the active RoutingSession.
        vehicle_id: Vehicle identifier (e.g. 'Van-1').
        delivered_stop_id: Stop or parcel ID that was successfully delivered.
        current_time_min: Timestamp in simulated minutes since midnight.
        db: Optional Motor database handle.

    Returns:
        Dict containing re-tuning outcome, updated schedule, and execution time in ms.
    """
    t0 = time.perf_counter()
    if db is None:
        db = get_db()

    obj_id = ObjectId(session_id) if isinstance(session_id, str) else session_id
    session = await db["routing_sessions"].find_one({"_id": obj_id})

    if not session:
        log.warning("Session %s not found for retune.", session_id)
        return {"success": False, "tier": "delivered_retune", "execution_time_ms": 0.0}

    assignments = session.get("vehicle_assignments", [])
    target_idx = None
    target_assignment = None

    for idx, a in enumerate(assignments):
        if a.get("vehicle_id") == vehicle_id:
            target_idx = idx
            target_assignment = a
            break

    if target_assignment is None:
        log.warning("Vehicle %s not found in session %s.", vehicle_id, session_id)
        return {"success": False, "tier": "delivered_retune", "execution_time_ms": 0.0}

    # Extract remaining stops
    all_stops = target_assignment.get("stops", [])
    remaining_stops = [s for s in all_stops if str(s) != str(delivered_stop_id)]

    # Fetch parcels SLA windows
    parcels_cursor = db["parcels"].find()
    parcels_docs = await parcels_cursor.to_list(length=300)
    sla_lookup: dict[str, tuple[int, int]] = {}
    for p in parcels_docs:
        pid = str(p.get("_id", p.get("parcel_id", "P-UNKNOWN")))
        sla_lookup[pid] = (p.get("sla_start_min", 540), p.get("sla_deadline_min", 1020))
        if "parcel_id" in p:
            sla_lookup[str(p["parcel_id"])] = (p.get("sla_start_min", 540), p.get("sla_deadline_min", 1020))

    wh_id = target_assignment.get("warehouse_id", "WH-PUNE-001")

    # Run ONLY QPSO continuous optimization on remaining stops (no QGA)
    if remaining_stops:
        decoded_routes = {
            vehicle_id: [
                {
                    "stops": remaining_stops,
                    "warehouse_id": wh_id,
                }
            ]
        }
        qpso_res = run_qpso(
            decoded_routes=decoded_routes,
            sla_lookup=sla_lookup,
            num_particles=15,
            max_iterations=25,
            bounds=(max(360.0, current_time_min), 1200.0),
            preset=session.get("preset", "balanced"),
            seed=42,
        )

        simulated_trips = qpso_res.simulated_routes.get(vehicle_id, [])
        if simulated_trips:
            trip = simulated_trips[0]
            updated_stop_arrivals = [
                {
                    "stop_id": s.stop_id,
                    "arrival_time_min": round(s.arrival_time_min, 1),
                    "departure_time_min": round(s.departure_time_min, 1),
                }
                for s in trip.stop_arrivals
            ]
            target_assignment["departure_time_min"] = round(trip.departure_time_min, 1)
            target_assignment["return_arrival_time_min"] = round(trip.return_arrival_time_min, 1)
            target_assignment["total_duration_min"] = round(trip.total_duration_min, 1)
            target_assignment["stops"] = remaining_stops
            target_assignment["stop_arrivals"] = updated_stop_arrivals
            target_assignment["feasible"] = qpso_res.feasible
    else:
        # All stops completed
        target_assignment["stops"] = []
        target_assignment["stop_arrivals"] = []
        target_assignment["status"] = "complete"

    # Update database
    assignments[target_idx] = target_assignment
    await db["routing_sessions"].update_one(
        {"_id": obj_id},
        {"$set": {"vehicle_assignments": assignments}},
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    log.info(
        "Tier 1 (Delivered Re-tune) completed for %s in %.2f ms (Feasible: %s)",
        vehicle_id,
        elapsed_ms,
        target_assignment.get("feasible", True),
    )

    return {
        "success": True,
        "tier": "delivered_retune",
        "vehicle_id": vehicle_id,
        "remaining_stops_count": len(remaining_stops),
        "execution_time_ms": round(elapsed_ms, 2),
    }
