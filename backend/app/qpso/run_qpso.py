"""
backend/app/qpso/run_qpso.py — Milestone 4.2

Orchestrates the Quantum Particle Swarm Optimization (QPSO) swarm loop
for continuous vehicle departure timing and hard SLA feasibility checking per spec §3d.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any

from app.costing.presets import CostWeights
from app.qpso.arrival_simulator import TripArrivalResult, simulate_fleet_arrivals
from app.qpso.fitness import calculate_qpso_fitness, check_trip_sla_feasibility
from app.qpso.particle import QPSOParticle, compute_mbest

log = logging.getLogger(__name__)


@dataclass
class QPSOResult:
    """Encapsulates the complete result of QPSO timing optimization."""
    feasible: bool
    best_departure_times: dict[str, float]
    best_fitness: float
    simulated_routes: dict[str, list[TripArrivalResult]]
    infeasible_routes: list[dict[str, Any]]
    per_vehicle_metrics: dict[str, Any] = field(default_factory=dict)
    iterations_completed: int = 0
    execution_time_ms: float = 0.0


def run_qpso(
    decoded_routes: dict[str, list[dict[str, Any]]],
    sla_lookup: dict[str, tuple[int, int] | dict[str, int]],
    travel_time_lookup: dict[tuple[str, str], float] | None = None,
    congestion_lookup: dict[tuple[str, str], float] | None = None,
    num_particles: int = 25,
    max_iterations: int = 40,
    bounds: tuple[float, float] = (360.0, 1200.0),  # 06:00 to 20:00
    beta_start: float = 1.0,
    beta_end: float = 0.5,
    preset: str | CostWeights = "balanced",
    seed: int | None = 42,
) -> QPSOResult:
    """
    Run QPSO optimization loop to determine optimal vehicle dispatch departure times.

    Args:
        decoded_routes: Output of decode_chromosome(): {vehicle_id: [trip_dict, ...]}.
        sla_lookup: Mapping stop_id -> SLA delivery window.
        travel_time_lookup: Precomputed baseline edge travel times in minutes.
        congestion_lookup: Precomputed edge congestion factors.
        num_particles: Number of quantum particles in swarm.
        max_iterations: Maximum swarm evolution iterations.
        bounds: Earliest and latest allowed departure time (minutes since midnight).
        beta_start: Initial contraction-expansion coefficient.
        beta_end: Final contraction-expansion coefficient.
        preset: Session cost weighting preset.
        seed: Random seed for deterministic reproducibility.

    Returns:
        QPSOResult dataclass containing binary feasibility flag and departure schedule.
    """
    t0 = time.perf_counter()
    rng = random.Random(seed)

    # Count total vehicle trips (dimensions)
    vehicle_trip_keys: list[tuple[str, int]] = []
    for v_id, trips in decoded_routes.items():
        for t_idx, _t in enumerate(trips):
            vehicle_trip_keys.append((v_id, t_idx))

    dim = len(vehicle_trip_keys)

    if dim == 0:
        return QPSOResult(
            feasible=True,
            best_departure_times={},
            best_fitness=0.0,
            simulated_routes={},
            infeasible_routes=[],
            iterations_completed=0,
            execution_time_ms=0.0,
        )

    # 1. Initialize Swarm
    min_b, max_b = bounds
    particles: list[QPSOParticle] = []
    for _ in range(num_particles):
        initial_pos = [rng.uniform(min_b, max_b) for _ in range(dim)]
        particles.append(QPSOParticle(position=initial_pos, bounds=bounds))

    def evaluate_pos(pos: list[float]) -> tuple[float, dict[str, list[TripArrivalResult]]]:
        # Map flat position vector to {vehicle_id: dep_time}
        dep_dict: dict[str, float] = {}
        for (v_id, _t_idx), dep_val in zip(vehicle_trip_keys, pos, strict=True):
            dep_dict[v_id] = dep_val

        sim_routes = simulate_fleet_arrivals(
            decoded_routes=decoded_routes,
            departure_times_min=dep_dict,
            travel_time_lookup=travel_time_lookup,
            congestion_lookup=congestion_lookup,
        )
        fit_eval = calculate_qpso_fitness(sim_routes, sla_lookup, preset=preset)
        return fit_eval["fitness"], sim_routes

    # Initial evaluation
    gbest_fitness = float("inf")
    gbest_position: list[float] = list(particles[0].position)

    for p in particles:
        fit, _ = evaluate_pos(p.position)
        p.update_pbest(fit)
        if fit < gbest_fitness:
            gbest_fitness = fit
            gbest_position = list(p.position)

    # 2. Main Swarm Evolution Loop
    for it in range(1, max_iterations + 1):
        # Linearly decreasing beta parameter for convergence
        beta = beta_start - ((it / max_iterations) * (beta_start - beta_end))
        mbest = compute_mbest(particles)

        for p in particles:
            p.update_quantum_position(
                gbest_position=gbest_position,
                mbest_position=mbest,
                beta=beta,
                seed=rng.randint(0, 1000000),
            )
            fit, _ = evaluate_pos(p.position)
            if p.update_pbest(fit):
                if fit < gbest_fitness:
                    gbest_fitness = fit
                    gbest_position = list(p.position)

    # 3. Final Evaluation with Global Best
    _, final_sim_routes = evaluate_pos(gbest_position)

    best_dep_times: dict[str, float] = {}
    for (v_id, _t_idx), dep_val in zip(vehicle_trip_keys, gbest_position, strict=True):
        best_dep_times[v_id] = round(dep_val, 2)

    # 4. Strict Hard SLA Feasibility Check
    infeasible_routes: list[dict[str, Any]] = []
    per_vehicle_metrics: dict[str, Any] = {}

    for v_id, trips in final_sim_routes.items():
        v_feasible = True
        v_violations = []
        for t_idx, trip in enumerate(trips):
            is_trip_feas, violations = check_trip_sla_feasibility(trip, sla_lookup)
            if not is_trip_feas:
                v_feasible = False
                infeasible_routes.append({
                    "vehicle_id": v_id,
                    "trip_index": t_idx,
                    "warehouse_id": decoded_routes[v_id][t_idx].get("warehouse_id"),
                    "stops": decoded_routes[v_id][t_idx].get("stops"),
                    "violations": violations,
                })
            v_violations.extend(violations)

        per_vehicle_metrics[v_id] = {
            "departure_time_min": best_dep_times.get(v_id),
            "feasible": v_feasible,
            "violations_count": len([v for v in v_violations if v["type"] == "late_violation"]),
            "total_duration_min": sum(t.total_duration_min for t in trips),
        }

    overall_feasible = len(infeasible_routes) == 0
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    log.info(
        "QPSO optimization: feasible=%s, best_fitness=%.2f, %d infeasible trips in %.2fms",
        overall_feasible,
        gbest_fitness,
        len(infeasible_routes),
        elapsed_ms,
    )

    return QPSOResult(
        feasible=overall_feasible,
        best_departure_times=best_dep_times,
        best_fitness=gbest_fitness,
        simulated_routes=final_sim_routes,
        infeasible_routes=infeasible_routes,
        per_vehicle_metrics=per_vehicle_metrics,
        iterations_completed=max_iterations,
        execution_time_ms=elapsed_ms,
    )
