"""
backend/app/pipeline/local_repair.py — Milestone 9.2

Tier 2 & Tier 3: "Failed" Event Handling — Local Repair & Escalation (Spec §3d, §9).
When a parcel delivery fails:
1. Tier 2: Searches existing routes for the nearest feasible insertion point using QPSO feasibility validation.
2. Tier 3: Escalates to a full QGA+QPSO re-optimization if no existing route can feasibly absorb the parcel.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from bson import ObjectId

from app.db import get_db
from app.pipeline.orchestrator import run_hybrid_routing_pipeline
from app.qpso.run_qpso import run_qpso

log = logging.getLogger(__name__)


async def repair_or_escalate_on_failed(
    session_id: str | ObjectId,
    failed_vehicle_id: str,
    failed_parcel_id: str,
    current_time_min: float,
    db: Any = None,
) -> dict[str, Any]:
    """
    Handle a failed delivery event: tries Tier 2 Local Repair first, escalating to Tier 3 Full QGA only if necessary.

    Args:
        session_id: ID of the active RoutingSession.
        failed_vehicle_id: Vehicle where the delivery attempt failed.
        failed_parcel_id: Stop or parcel ID that failed.
        current_time_min: Current simulated timestamp in minutes since midnight.
        db: Optional Motor database handle.

    Returns:
        Dict containing tier applied ('failed_local_repair' or 'escalation_full_qga'), outcome, and timing.
    """
    t0 = time.perf_counter()
    if db is None:
        db = get_db()

    obj_id = ObjectId(session_id) if isinstance(session_id, str) else session_id
    session = await db["routing_sessions"].find_one({"_id": obj_id})

    if not session:
        log.warning("Session %s not found for local repair.", session_id)
        return {"success": False, "tier": "failed_local_repair", "execution_time_ms": 0.0}

    assignments = session.get("vehicle_assignments", [])

    # Step 1: Remove failed parcel from original vehicle's remaining stops
    for a in assignments:
        if a.get("vehicle_id") == failed_vehicle_id:
            a["stops"] = [s for s in a.get("stops", []) if str(s) != str(failed_parcel_id)]
            a["stop_arrivals"] = [
                s for s in a.get("stop_arrivals", []) if str(s.get("stop_id")) != str(failed_parcel_id)
            ]

    # Lookups for parcels
    parcels_cursor = db["parcels"].find()
    parcels_docs = await parcels_cursor.to_list(length=300)
    sla_lookup: dict[str, tuple[int, int]] = {}
    for p in parcels_docs:
        pid = str(p.get("_id", p.get("parcel_id", "P-UNKNOWN")))
        sla_lookup[pid] = (p.get("sla_start_min", 540), p.get("sla_deadline_min", 1020))
        if "parcel_id" in p:
            sla_lookup[str(p["parcel_id"])] = (p.get("sla_start_min", 540), p.get("sla_deadline_min", 1020))

    wh_id = "WH-PUNE-001"
    if assignments and "warehouse_id" in assignments[0]:
        wh_id = assignments[0]["warehouse_id"]

    # Step 2: Search existing candidate vehicles for nearest feasible insertion (Tier 2)
    repaired_target_vehicle = None
    best_candidate_stops = None
    best_candidate_idx = None
    best_qpso_trip = None

    for idx, cand in enumerate(assignments):
        v_id = cand.get("vehicle_id")
        if v_id == failed_vehicle_id:
            continue  # Don't immediately re-assign to the same failing vehicle

        curr_stops = cand.get("stops", [])
        # Try inserting at each position in the candidate vehicle's route
        for ins_pos in range(len(curr_stops) + 1):
            trial_stops = curr_stops[:ins_pos] + [failed_parcel_id] + curr_stops[ins_pos:]

            decoded_routes = {
                v_id: [
                    {
                        "stops": trial_stops,
                        "warehouse_id": wh_id,
                    }
                ]
            }
            trial_qpso = run_qpso(
                decoded_routes=decoded_routes,
                sla_lookup=sla_lookup,
                num_particles=15,
                max_iterations=20,
                bounds=(max(360.0, current_time_min), 1200.0),
                preset=session.get("preset", "balanced"),
                seed=42,
            )

            if trial_qpso.feasible:
                # Feasible candidate insertion found!
                repaired_target_vehicle = v_id
                best_candidate_stops = trial_stops
                best_candidate_idx = idx
                trips = trial_qpso.simulated_routes.get(v_id, [])
                best_qpso_trip = trips[0] if trips else None
                break

        if repaired_target_vehicle:
            break

    # Tier 2 Success: Update target vehicle with inserted stop
    if repaired_target_vehicle and best_qpso_trip and best_candidate_idx is not None:
        target_a = assignments[best_candidate_idx]
        target_a["stops"] = best_candidate_stops
        target_a["stop_arrivals"] = [
            {
                "stop_id": s.stop_id,
                "arrival_time_min": round(s.arrival_time_min, 1),
                "departure_time_min": round(s.departure_time_min, 1),
            }
            for s in best_qpso_trip.stop_arrivals
        ]
        target_a["departure_time_min"] = round(best_qpso_trip.departure_time_min, 1)
        target_a["return_arrival_time_min"] = round(best_qpso_trip.return_arrival_time_min, 1)
        target_a["total_duration_min"] = round(best_qpso_trip.total_duration_min, 1)
        target_a["feasible"] = True

        assignments[best_candidate_idx] = target_a
        await db["routing_sessions"].update_one(
            {"_id": obj_id},
            {"$set": {"vehicle_assignments": assignments}},
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        log.info(
            "Tier 2 (Failed Local Repair) succeeded: Reassigned %s -> %s in %.2f ms",
            failed_parcel_id,
            repaired_target_vehicle,
            elapsed_ms,
        )
        return {
            "success": True,
            "tier": "failed_local_repair",
            "failed_parcel_id": failed_parcel_id,
            "reassigned_to_vehicle": repaired_target_vehicle,
            "execution_time_ms": round(elapsed_ms, 2),
        }

    # Step 3: Tier 3 Escalation — No feasible single-route insertion found, run full QGA+QPSO
    log.warning(
        "Tier 2 (Local Repair) found no feasible route for %s. Escalating to Tier 3 (Full QGA Re-run).",
        failed_parcel_id,
    )

    # Collect all unserved parcels across fleet + failed parcel
    unserved_pids = [failed_parcel_id]
    for a in assignments:
        for s in a.get("stops", []):
            unserved_pids.append(str(s))

    unserved_parcels = [p for p in parcels_docs if str(p.get("_id", p.get("parcel_id"))) in unserved_pids]
    if not unserved_parcels:
        unserved_parcels = parcels_docs[:10]

    warehouses_cursor = db["warehouses"].find()
    warehouses = await warehouses_cursor.to_list(length=10)
    vehicles_cursor = db["vehicles"].find()
    veh_docs = await vehicles_cursor.to_list(length=50)
    vehicles = [v.get("label", "Van-1") for v in veh_docs] if veh_docs else ["Van-1", "Van-2", "Van-3"]

    pipeline_res = await run_hybrid_routing_pipeline(
        parcels=unserved_parcels,
        warehouses=warehouses,
        vehicles=vehicles,
        preset=session.get("preset", "balanced"),
        max_bounceback_retries=2,
        seed=42,
        persist_to_db=False,
    )

    await db["routing_sessions"].update_one(
        {"_id": obj_id},
        {
            "$set": {
                "vehicle_assignments": pipeline_res.vehicle_assignments,
                "total_distance_km": pipeline_res.total_distance_km,
                "sla_compliance_pct": pipeline_res.sla_compliance_pct,
                "metadata.escalated_at_min": current_time_min,
                "metadata.fallback_applied": pipeline_res.fallback_applied,
            }
        },
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    log.info("Tier 3 (Full QGA Escalation) completed in %.2f ms", elapsed_ms)

    return {
        "success": True,
        "tier": "escalation_full_qga",
        "failed_parcel_id": failed_parcel_id,
        "reassigned_to_vehicle": "fleet_reoptimized",
        "fallback_applied": pipeline_res.fallback_applied,
        "execution_time_ms": round(elapsed_ms, 2),
    }
