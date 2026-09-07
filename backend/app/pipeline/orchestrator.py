"""
backend/app/pipeline/orchestrator.py — Milestone 4.3

Hybrid Optimization Pipeline Orchestrator:
Coordinates Leiden Pre-Clustering -> QGA (Combinatorial) -> QPSO (Timing/SLA) -> Bounce-Back Loop.
Persists complete session state to MongoDB `routing_sessions` collection per spec §7.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from app.clustering.leiden import cluster_stops
from app.db import get_db
from app.models.routing_session import SessionPreset, SessionStatus
from app.qga.run_qga import run_qga
from app.qpso.run_qpso import QPSOResult, run_qpso

log = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of the full hybrid routing pipeline."""
    session_id: str | None
    status: SessionStatus
    feasible: bool
    fallback_applied: bool
    total_distance_km: float
    sla_compliance_pct: float
    vehicle_assignments: list[dict[str, Any]]
    fitness_history: list[dict[str, Any]]
    bounceback_count: int
    cluster_results: list[dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0.0


async def run_hybrid_routing_pipeline(
    parcels: list[dict[str, Any]],
    warehouses: list[dict[str, Any]] | None = None,
    vehicles: list[str] | None = None,
    preset: str | SessionPreset = SessionPreset.BALANCED,
    max_bounceback_retries: int = 3,
    travel_time_lookup: dict[tuple[str, str], float] | None = None,
    congestion_lookup: dict[tuple[str, str], float] | None = None,
    seed: int | None = 42,
    persist_to_db: bool = True,
    db: Any = None,
) -> PipelineResult:
    """
    Run end-to-end multi-stage routing optimization with targeted bounce-back feedback.

    Args:
        parcels: List of active parcel documents.
        warehouses: List of available warehouse documents.
        vehicles: List of available vehicle IDs across fleet.
        preset: Optimization preset ('balanced', 'min_distance', 'min_fuel', 'prioritize_sla').
        max_bounceback_retries: Maximum QGA-QPSO bounce-back attempts per cluster.
        travel_time_lookup: Optional distance/travel time matrix.
        congestion_lookup: Optional congestion factor matrix.
        seed: Random seed for deterministic reproducibility.
        persist_to_db: Whether to write session result into MongoDB routing_sessions.
        db: Optional Motor database handle.

    Returns:
        PipelineResult containing final routes, metrics, and persistence ID.
    """
    t0 = time.perf_counter()
    preset_str = str(preset).lower()

    # Map preset string to valid SessionPreset enum
    if "dist" in preset_str:
        session_preset = SessionPreset.MIN_DISTANCE
    elif "fuel" in preset_str or "cost" in preset_str:
        session_preset = SessionPreset.MIN_FUEL
    elif "sla" in preset_str:
        session_preset = SessionPreset.PRIORITIZE_SLA
    else:
        session_preset = SessionPreset.BALANCED

    if not vehicles:
        vehicles = [f"VEH-{i:03d}" for i in range(1, 21)]

    # 1. Leiden Community Pre-Clustering (Milestone 2.2)
    clustering_res = cluster_stops(parcels, warehouses, resolution=1.0, seed=seed)
    n_clusters = clustering_res.cluster_count

    log.info(
        "Pipeline Start: %d parcels partitioned into %d clusters across %d vehicles",
        len(parcels),
        n_clusters,
        len(vehicles),
    )

    # 2. Build lookups
    sla_lookup: dict[str, Any] = {}
    stop_weights: dict[str, float] = {}
    for p in parcels:
        tn = p.get("tracking_number") or p.get("parcel_id") or "UNKNOWN"
        sla_lookup[tn] = p.get("sla_window", (540, 1020))
        stop_weights[tn] = float(p.get("weight_kg", 5.0))

    wh_id = "WH-PUNE-001"
    if warehouses and len(warehouses) > 0:
        wh_id = warehouses[0].get("warehouse_id", "WH-PUNE-001")

    # Allocate vehicles across clusters
    cluster_vehicle_map: dict[int, list[str]] = {}
    cluster_ids = list(clustering_res.clusters.keys())
    if cluster_ids:
        veh_per_cluster = max(1, len(vehicles) // len(cluster_ids))
        for idx, c_id in enumerate(cluster_ids):
            start_v = idx * veh_per_cluster
            end_v = start_v + veh_per_cluster if idx < len(cluster_ids) - 1 else len(vehicles)
            assigned_v = vehicles[start_v:end_v]
            cluster_vehicle_map[c_id] = assigned_v if assigned_v else [vehicles[0]]

    # 3. Solve each cluster with QGA -> QPSO and Bounce-Back Feedback
    overall_feasible = True
    any_fallback_applied = False
    total_bouncebacks = 0
    all_vehicle_assignments: list[dict[str, Any]] = []
    all_fitness_history: list[dict[str, Any]] = []
    cluster_results: list[dict[str, Any]] = []
    total_distance_km = 0.0
    total_stops_count = len(parcels)
    total_violations_count = 0

    for c_id, c_parcels in clustering_res.clusters.items():
        c_stop_ids = [p.get("tracking_number") or p.get("parcel_id") for p in c_parcels]
        c_vehicles = cluster_vehicle_map.get(c_id, [vehicles[0]])

        # Initial QGA pass
        qga_res = run_qga(
            stops=c_stop_ids,
            stop_weights_kg=stop_weights,
            distance_lookup=travel_time_lookup,
            vehicles=c_vehicles,
            warehouse_id=wh_id,
            preset=session_preset.value,
            seed=seed,
        )

        # Initial QPSO timing pass
        qpso_res: QPSOResult = run_qpso(
            decoded_routes=qga_res.decoded_routes,
            sla_lookup=sla_lookup,
            travel_time_lookup=travel_time_lookup,
            congestion_lookup=congestion_lookup,
            preset=session_preset.value,
            seed=seed,
        )

        cluster_bouncebacks = 0
        fallback_applied_for_cluster = False

        # Infeasibility Bounce-Back Loop
        while not qpso_res.feasible and cluster_bouncebacks < max_bounceback_retries:
            cluster_bouncebacks += 1
            total_bouncebacks += 1
            log.info(
                "Cluster %d: Infeasible route detected. Triggering targeted QGA bounce-back retry %d/%d...",
                c_id,
                cluster_bouncebacks,
                max_bounceback_retries,
            )

            # Re-run QGA with perturbed seed and increased generations
            retry_seed = (seed or 42) + (cluster_bouncebacks * 100)
            qga_res = run_qga(
                stops=c_stop_ids,
                stop_weights_kg=stop_weights,
                distance_lookup=travel_time_lookup,
                vehicles=c_vehicles,
                warehouse_id=wh_id,
                max_generations=50 + (cluster_bouncebacks * 20),
                mutation_rate=0.25 + (cluster_bouncebacks * 0.05),
                preset=session_preset.value,
                seed=retry_seed,
            )

            qpso_res = run_qpso(
                decoded_routes=qga_res.decoded_routes,
                sla_lookup=sla_lookup,
                travel_time_lookup=travel_time_lookup,
                congestion_lookup=congestion_lookup,
                max_iterations=40 + (cluster_bouncebacks * 15),
                preset=session_preset.value,
                seed=retry_seed,
            )

        if not qpso_res.feasible:
            # Reached retry cap: Apply Best-Effort Fallback (never drop parcels)
            fallback_applied_for_cluster = True
            any_fallback_applied = True
            overall_feasible = False
            log.warning(
                "Cluster %d: Bounce-back cap (%d) reached. Applying best-effort fallback with explicit violation flags.",
                c_id,
                max_bounceback_retries,
            )

        # Aggregate cluster metrics
        for v_id, trips in qpso_res.simulated_routes.items():
            for trip in trips:
                stops_in_trip = [s.stop_id for s in trip.stop_arrivals]
                # Sum distance
                prev = wh_id
                for s in stops_in_trip:
                    total_distance_km += (travel_time_lookup.get((prev, s), 1.0) if travel_time_lookup else 1.0)
                    prev = s
                total_distance_km += (travel_time_lookup.get((prev, wh_id), 1.0) if travel_time_lookup else 1.0)

                # Check violations
                for arr in trip.stop_arrivals:
                    sla = sla_lookup.get(arr.stop_id, (540, 1020))
                    end_min = float(sla.get("end_time", 1020)) if isinstance(sla, dict) else float(sla[1])
                    if arr.arrival_time_min > end_min:
                        total_violations_count += 1

                all_vehicle_assignments.append({
                    "vehicle_id": v_id,
                    "cluster_id": c_id,
                    "warehouse_id": wh_id,
                    "departure_time_min": trip.departure_time_min,
                    "return_arrival_time_min": trip.return_arrival_time_min,
                    "total_duration_min": trip.total_duration_min,
                    "stops": stops_in_trip,
                    "stop_arrivals": [
                        {
                            "stop_id": s.stop_id,
                            "arrival_time_min": s.arrival_time_min,
                            "departure_time_min": s.departure_time_min,
                        }
                        for s in trip.stop_arrivals
                    ],
                    "fallback_applied": fallback_applied_for_cluster,
                    "feasible": len(qpso_res.infeasible_routes) == 0,
                })

        all_fitness_history.extend(qga_res.fitness_history)
        cluster_results.append({
            "cluster_id": c_id,
            "stop_count": len(c_stop_ids),
            "feasible": qpso_res.feasible,
            "bounceback_retries": cluster_bouncebacks,
            "fallback_applied": fallback_applied_for_cluster,
            "best_qga_fitness": qga_res.best_fitness,
            "best_qpso_fitness": qpso_res.best_fitness,
        })

    # Compute SLA compliance %
    if total_stops_count > 0:
        compliant_stops = max(0, total_stops_count - total_violations_count)
        sla_compliance_pct = round((compliant_stops / total_stops_count) * 100.0, 1)
    else:
        sla_compliance_pct = 100.0

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    session_status = SessionStatus.COMPLETED

    session_doc = {
        "preset": session_preset.value,
        "status": session_status.value,
        "created_at": time.time(),
        "cluster_count": n_clusters,
        "vehicle_assignments": all_vehicle_assignments,
        "fitness_history": all_fitness_history,
        "total_distance_km": round(total_distance_km, 2),
        "sla_compliance_pct": sla_compliance_pct,
        "seeded": False,
        "metadata": {
            "feasible": overall_feasible,
            "fallback_applied": any_fallback_applied,
            "bounceback_count": total_bouncebacks,
            "execution_time_ms": elapsed_ms,
            "cluster_results": cluster_results,
        },
    }

    session_id: str | None = None
    if persist_to_db:
        try:
            target_db = db if db is not None else get_db()
            insert_res = await target_db.routing_sessions.insert_one(session_doc)
            session_id = str(insert_res.inserted_id)
            log.info("Persisted routing session %s to MongoDB", session_id)
        except Exception as e:
            log.warning("Could not persist routing session to DB: %s", e)

    return PipelineResult(
        session_id=session_id,
        status=session_status,
        feasible=overall_feasible,
        fallback_applied=any_fallback_applied,
        total_distance_km=round(total_distance_km, 2),
        sla_compliance_pct=sla_compliance_pct,
        vehicle_assignments=all_vehicle_assignments,
        fitness_history=all_fitness_history,
        bounceback_count=total_bouncebacks,
        cluster_results=cluster_results,
        execution_time_ms=elapsed_ms,
    )
