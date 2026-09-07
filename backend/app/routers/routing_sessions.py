"""
backend/app/routers/routing_sessions.py — Milestone 6.2

Routing optimization endpoints:
- POST /routing-sessions/run (pipeline trigger with preset selection)
- GET /routing-sessions/{id}/status (execution status polling)
- GET /routing-sessions/{id} (fetch completed route results & metrics)
- POST /routing-sessions/{id}/assign (commit suggested routes to vehicles)
"""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from app.costing.presets import PRESETS, get_preset_weights
from app.db import get_db
from app.pipeline.orchestrator import run_hybrid_routing_pipeline

router = APIRouter(prefix="/routing-sessions", tags=["Routing Sessions"])


def _normalize_preset_name(preset: str) -> str:
    """Normalize input preset name to standard MongoDB enum."""
    preset_lower = preset.strip().lower().replace("-", "_")
    if "dist" in preset_lower:
        return "min_distance"
    elif "fuel" in preset_lower or "cost" in preset_lower:
        return "min_fuel"
    elif "sla" in preset_lower:
        return "prioritize_sla"
    return "balanced"


class RoutingRunRequest(BaseModel):
    """Payload to trigger a routing optimization run."""

    preset: str = Field("balanced", description="Business preset name: balanced, min_distance, min_fuel, prioritize_sla")
    warehouse_id: str | None = Field(None, description="Optional target warehouse ObjectId")
    max_bounceback_retries: int = Field(3, ge=0, le=10, description="Maximum QGA-QPSO bounceback retries")
    seed: int | None = Field(42, description="Random seed for deterministic optimization")
    async_run: bool = Field(False, description="Run in background task if True")


class RoutingRunResponse(BaseModel):
    """Response returned when routing run is triggered."""

    session_id: str
    status: str
    message: str


class SessionStatusResponse(BaseModel):
    """Lightweight polling status response."""

    session_id: str
    status: str
    progress_percent: int
    elapsed_seconds: float
    error_message: str | None = None


class AssignRoutesResponse(BaseModel):
    """Response returned when routes are confirmed and assigned."""

    session_id: str
    status: str
    assigned_vehicles_count: int
    assigned_parcels_count: int


async def _execute_pipeline_and_update(
    session_id: ObjectId,
    parcels: list[dict[str, Any]],
    warehouses: list[dict[str, Any]],
    vehicles: list[str],
    preset: str,
    max_bounceback_retries: int,
    seed: int | None,
):
    """Background or inline worker executing the full pipeline."""
    db = get_db()
    try:
        pipeline_res = await run_hybrid_routing_pipeline(
            parcels=parcels,
            warehouses=warehouses,
            vehicles=vehicles,
            preset=preset,
            max_bounceback_retries=max_bounceback_retries,
            seed=seed,
            persist_to_db=False,  # We update the pre-allocated session record
        )
        await db["routing_sessions"].update_one(
            {"_id": session_id},
            {
                "$set": {
                    "status": "completed",
                    "cluster_count": len(pipeline_res.cluster_results),
                    "vehicle_assignments": pipeline_res.vehicle_assignments,
                    "fitness_history": pipeline_res.fitness_history,
                    "total_distance_km": pipeline_res.total_distance_km,
                    "sla_compliance_pct": pipeline_res.sla_compliance_pct,
                    "metadata": {
                        "feasible": pipeline_res.feasible,
                        "fallback_applied": pipeline_res.fallback_applied,
                        "bounceback_count": pipeline_res.bounceback_count,
                        "execution_time_ms": pipeline_res.execution_time_ms,
                        "cluster_results": pipeline_res.cluster_results,
                    },
                }
            },
        )
    except Exception as exc:
        await db["routing_sessions"].update_one(
            {"_id": session_id},
            {
                "$set": {
                    "status": "failed",
                    "error_message": str(exc),
                }
            },
        )


@router.post("/run", response_model=RoutingRunResponse, status_code=status.HTTP_200_OK)
async def run_routing_session(req: RoutingRunRequest, background_tasks: BackgroundTasks):
    """
    Trigger end-to-end QGA + QPSO optimization run with a selected business preset.
    """
    # Validate preset name against known presets
    try:
        get_preset_weights(req.preset)
    except KeyError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid preset '{req.preset}'. Valid options are: {list(PRESETS.keys())}",
        ) from exc

    normalized_preset = _normalize_preset_name(req.preset)
    db = get_db()

    # Fetch parcels from database
    parcels_cursor = db["parcels"].find({"status": {"$ne": "delivered"}})
    parcels = await parcels_cursor.to_list(length=200)

    # If database has no parcels, create synthetic stops for demo
    if not parcels:
        parcels = [
            {
                "parcel_id": f"P-{i:03d}",
                "address": f"Delivery Point #{i}, Pune",
                "lat": 18.5204 + (i % 5) * 0.01,
                "lon": 73.8567 + (i % 4) * 0.01,
                "weight_kg": 5.0,
                "sla_window": (540, 900),
            }
            for i in range(1, 21)
        ]
    else:
        # Standardize parcel keys for pipeline
        for p in parcels:
            p["parcel_id"] = str(p.get("_id", p.get("parcel_id", "P-UNKNOWN")))
            if "sla_start_min" in p and "sla_deadline_min" in p:
                p["sla_window"] = (p["sla_start_min"], p["sla_deadline_min"])

    # Fetch warehouses
    wh_cursor = db["warehouses"].find()
    warehouses = await wh_cursor.to_list(length=10)

    # Fetch vehicles
    veh_cursor = db["vehicles"].find()
    veh_docs = await veh_cursor.to_list(length=50)
    vehicles = [v.get("label", f"Van-{idx+1}") for idx, v in enumerate(veh_docs)] if veh_docs else [f"Van-{i}" for i in range(1, 4)]

    # Pre-allocate session in MongoDB
    session_doc = {
        "preset": normalized_preset,
        "status": "running",
        "created_at": 1788780000.0,
        "cluster_count": None,
        "vehicle_assignments": [],
        "fitness_history": [],
        "total_distance_km": None,
        "sla_compliance_pct": None,
        "seeded": False,
        "metadata": {},
    }
    insert_res = await db["routing_sessions"].insert_one(session_doc)
    session_id = insert_res.inserted_id

    if req.async_run:
        background_tasks.add_task(
            _execute_pipeline_and_update,
            session_id,
            parcels,
            warehouses,
            vehicles,
            normalized_preset,
            req.max_bounceback_retries,
            req.seed,
        )
        return RoutingRunResponse(
            session_id=str(session_id),
            status="running",
            message="Routing optimization pipeline started in background.",
        )
    else:
        await _execute_pipeline_and_update(
            session_id,
            parcels,
            warehouses,
            vehicles,
            normalized_preset,
            req.max_bounceback_retries,
            req.seed,
        )
        return RoutingRunResponse(
            session_id=str(session_id),
            status="completed",
            message="Routing optimization pipeline completed successfully.",
        )


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """Lightweight polling endpoint to check pipeline run status."""
    try:
        obj_id = ObjectId(session_id)
    except InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing session with ID '{session_id}' not found.",
        ) from exc

    db = get_db()
    doc = await db["routing_sessions"].find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing session with ID '{session_id}' not found.",
        )

    st = doc.get("status", "completed")
    progress = 100 if st == "completed" else (50 if st == "running" else 0)
    exec_ms = doc.get("metadata", {}).get("execution_time_ms", 0.0)

    return SessionStatusResponse(
        session_id=str(doc["_id"]),
        status=st,
        progress_percent=progress,
        elapsed_seconds=round(exec_ms / 1000.0, 3),
        error_message=doc.get("error_message"),
    )


@router.get("/{session_id}", response_model=dict[str, Any])
async def get_session_details(session_id: str):
    """Retrieve full routing session solution, routes, and metrics."""
    try:
        obj_id = ObjectId(session_id)
    except InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing session with ID '{session_id}' not found.",
        ) from exc

    db = get_db()
    doc = await db["routing_sessions"].find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing session with ID '{session_id}' not found.",
        )

    doc["id"] = str(doc.pop("_id"))
    return doc


@router.post("/{session_id}/assign", response_model=AssignRoutesResponse)
async def assign_session_routes(session_id: str):
    """Confirm and assign suggested routes to vehicles and parcels."""
    try:
        obj_id = ObjectId(session_id)
    except InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing session with ID '{session_id}' not found.",
        ) from exc

    db = get_db()
    doc = await db["routing_sessions"].find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing session with ID '{session_id}' not found.",
        )

    assignments = doc.get("vehicle_assignments", [])
    assigned_vehicles = {a["vehicle_id"] for a in assignments if "vehicle_id" in a}
    assigned_parcels = set()
    for a in assignments:
        for s in a.get("stops", []):
            assigned_parcels.add(s)

    # Update vehicle statuses to en_route
    if assigned_vehicles:
        await db["vehicles"].update_many(
            {"label": {"$in": list(assigned_vehicles)}},
            {"$set": {"status": "en_route"}},
        )

    # Update parcel statuses to assigned
    if assigned_parcels:
        valid_obj_ids = []
        for pid in assigned_parcels:
            try:
                valid_obj_ids.append(ObjectId(pid))
            except Exception:
                pass
        if valid_obj_ids:
            await db["parcels"].update_many(
                {"_id": {"$in": valid_obj_ids}},
                {"$set": {"status": "assigned"}},
            )

    # Update session assignment status
    await db["routing_sessions"].update_one(
        {"_id": obj_id},
        {"$set": {"assigned": True, "status": "completed"}},
    )

    return AssignRoutesResponse(
        session_id=str(doc["_id"]),
        status="assigned",
        assigned_vehicles_count=len(assigned_vehicles),
        assigned_parcels_count=len(assigned_parcels),
    )
