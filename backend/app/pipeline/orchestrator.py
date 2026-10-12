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

import math
from app.clustering.leiden import cluster_stops
from app.db import get_db
from app.models.routing_session import SessionPreset, SessionStatus
from app.qga.run_qga import run_qga
from app.qpso.run_qpso import QPSOResult, run_qpso
from app.routing.osrm import fetch_osrm_route_geometry

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def _extract_parcel_coords(p: dict) -> tuple[float, float]:
    lat = p.get("lat")
    lon = p.get("lon")
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    loc = p.get("location")
    if isinstance(loc, dict) and "coordinates" in loc:
        coords = loc["coordinates"]
        if len(coords) >= 2:
            return float(coords[1]), float(coords[0])
    return 18.5204, 73.8567

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
    vehicles: list[dict[str, Any]] | None = None,
    preset: str | SessionPreset = SessionPreset.BALANCED,
    max_bounceback_retries: int = 3,
    travel_time_lookup: dict[tuple[str, str], float] | None = None,
    congestion_lookup: dict[tuple[str, str], float] | None = None,
    seed: int | None = 42,
    persist_to_db: bool = True,
    preview: bool = False,   # If True, session is a comparison preview and excluded from history
    db: Any = None,
) -> PipelineResult:
    """
    Run end-to-end multi-stage routing optimization with targeted bounce-back feedback.

    Args:
        parcels: List of active parcel documents.
        warehouses: List of available warehouse documents.
        vehicles: List of available vehicle dicts across fleet.
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
        vehicles = [{"label": f"VEH-{i:03d}"} for i in range(1, 21)]

    normalized_vehicles: list[dict[str, Any]] = []
    for i, v in enumerate(vehicles):
        if isinstance(v, str):
            normalized_vehicles.append({"label": v})
        elif isinstance(v, dict):
            normalized_vehicles.append(v)
        else:
            normalized_vehicles.append({"label": getattr(v, "label", f"VEH-{i:03d}")})

    vehicle_ids = [v.get("label", f"VEH-{i:03d}") for i, v in enumerate(normalized_vehicles)]
    vehicle_lookup = {v.get("label", f"VEH-{i:03d}"): v for i, v in enumerate(normalized_vehicles)}

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
        veh_per_cluster = max(1, len(vehicle_ids) // len(cluster_ids))
        for idx, c_id in enumerate(cluster_ids):
            start_v = idx * veh_per_cluster
            end_v = start_v + veh_per_cluster if idx < len(cluster_ids) - 1 else len(vehicle_ids)
            assigned_v = vehicle_ids[start_v:end_v]
            cluster_vehicle_map[c_id] = assigned_v if assigned_v else [vehicle_ids[0]]

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
    parcel_info = {}
    for p in parcels:
        key = str(p.get("tracking_number") or p.get("parcel_id") or p.get("id") or "")
        plat, plon = _extract_parcel_coords(p)
        parcel_info[key] = {
            "lat": plat,
            "lon": plon,
            "address": p.get("address", ""),
            "recipient": p.get("recipient", ""),
        }

    for c_id, c_parcels in clustering_res.clusters.items():
        c_stop_ids = [p.get("tracking_number") or p.get("parcel_id") for p in c_parcels]
        c_vehicles = cluster_vehicle_map.get(c_id, [vehicle_ids[0]])

        # Select closest warehouse for this cluster centroid
        c_wh = warehouses[0] if warehouses else {"warehouse_id": "WH-PUNE-001", "lat": 18.5308, "lon": 73.8475}
        if warehouses and len(warehouses) > 1 and c_parcels:
            c_lat = sum(_extract_parcel_coords(p)[0] for p in c_parcels) / len(c_parcels)
            c_lon = sum(_extract_parcel_coords(p)[1] for p in c_parcels) / len(c_parcels)
            c_wh = min(

                warehouses,
                key=lambda w: _haversine(c_lat, c_lon, float(w.get("lat", 18.52)), float(w.get("lon", 73.85)))
            )
        cluster_wh_id = c_wh.get("warehouse_id") or c_wh.get("id") or "WH-PUNE-001"
        cluster_wh_lat = float(c_wh.get("lat", 18.5308))
        cluster_wh_lon = float(c_wh.get("lon", 73.8475))

        # Initial QGA pass
        qga_res = run_qga(
            stops=c_stop_ids,
            stop_weights_kg=stop_weights,
            distance_lookup=travel_time_lookup,
            vehicles=c_vehicles,
            warehouse_id=cluster_wh_id,
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

            # Re-run QGA with perturbed seed
            retry_seed = (seed or 42) + cluster_bouncebacks * 17
            qga_res = run_qga(
                stops=c_stop_ids,
                stop_weights_kg=stop_weights,
                distance_lookup=travel_time_lookup,
                vehicles=c_vehicles,
                warehouse_id=cluster_wh_id,
                preset=session_preset.value,
                seed=retry_seed,
            )

            qpso_res = run_qpso(
                decoded_routes=qga_res.decoded_routes,
                sla_lookup=sla_lookup,
                travel_time_lookup=travel_time_lookup,
                congestion_lookup=congestion_lookup,
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
            veh_obj = vehicle_lookup.get(v_id, {})
            start_lat = veh_obj.get("start_lat")
            start_lon = veh_obj.get("start_lon")
            wh_lat = cluster_wh_lat
            wh_lon = cluster_wh_lon
            
            repo_distance_km = 0.0
            if start_lat is not None and start_lon is not None:
                repo_distance_km = _haversine(start_lat, start_lon, wh_lat, wh_lon) * 1.3
            
            total_distance_km += repo_distance_km

            for trip in trips:
                stops_in_trip = [s.stop_id for s in trip.stop_arrivals]

                # Check violations
                for arr in trip.stop_arrivals:
                    sla = sla_lookup.get(arr.stop_id, (540, 1020))
                    end_min = float(sla.get("end_time", 1020)) if isinstance(sla, dict) else float(sla[1])
                    if arr.arrival_time_min > end_min:
                        total_violations_count += 1
                        
                # Build waypoints for OSRM fetch
                waypoints = [{"lat": wh_lat, "lon": wh_lon}]
                parcel_coords = {
                    str(p.get("tracking_number") or p.get("parcel_id") or p.get("id") or ""): _extract_parcel_coords(p)
                    for p in parcels
                }
                for s in stops_in_trip:
                    if s in parcel_coords and parcel_coords[s][0]:
                        waypoints.append({"lat": parcel_coords[s][0], "lon": parcel_coords[s][1]})
                waypoints.append({"lat": wh_lat, "lon": wh_lon})

                
                route_geom_res = await fetch_osrm_route_geometry(waypoints)
                trip_dist_km = route_geom_res.get("distance_km", 0.0)
                if trip_dist_km <= 0.0 and len(waypoints) > 1:
                    trip_dist_km = sum(_haversine(waypoints[i]["lat"], waypoints[i]["lon"], waypoints[i+1]["lat"], waypoints[i+1]["lon"]) * 1.3 for i in range(len(waypoints)-1))
                
                total_distance_km += trip_dist_km

                all_vehicle_assignments.append({
                    "vehicle_id": v_id,
                    "cluster_id": c_id,
                    "warehouse_id": cluster_wh_id,
                    "departure_time_min": trip.departure_time_min,
                    "return_arrival_time_min": trip.return_arrival_time_min,
                    "total_duration_min": trip.total_duration_min,
                    "distance_km": round(trip_dist_km, 2),
                    "repositioning_distance_km": repo_distance_km,
                    "stops": stops_in_trip,
                    "stop_arrivals": [
                        {
                            "stop_id": s.stop_id,
                            "arrival_time_min": s.arrival_time_min,
                            "departure_time_min": s.departure_time_min,
                            "lat": parcel_info.get(s.stop_id, {}).get("lat"),
                            "lon": parcel_info.get(s.stop_id, {}).get("lon"),
                            "address": parcel_info.get(s.stop_id, {}).get("address"),
                        }
                        for s in trip.stop_arrivals
                    ],
                    "route_geometry": route_geom_res.get("coordinates", []),
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
        "preview": preview,  # True = comparison preview; excluded from session history
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
