"""
backend/app/qpso/fitness.py — Milestone 4.2

QPSO continuous fitness evaluation and hard SLA feasibility checking per spec §3d / §2a.
Evaluates total travel duration plus w4-weighted SLA violations, while maintaining
strict binary feasibility verification (SLA is a hard constraint).
"""

from __future__ import annotations

from typing import Any

from app.costing.presets import CostWeights, get_preset_weights
from app.qpso.arrival_simulator import TripArrivalResult


def check_trip_sla_feasibility(
    trip_result: TripArrivalResult,
    sla_lookup: dict[str, tuple[int, int] | dict[str, int]],
    grace_period_min: float = 0.0,
) -> tuple[bool, list[dict[str, Any]]]:
    """
    Perform a strict hard SLA feasibility check on all stops within a simulated trip.

    Args:
        trip_result: TripArrivalResult object from arrival simulator.
        sla_lookup: Mapping stop_id -> (start_time, end_time) or {'start_time': ..., 'end_time': ...}.
        grace_period_min: Optional grace period in minutes.

    Returns:
        tuple[bool, list[dict]]: (is_feasible, list_of_violations)
    """
    violations: list[dict[str, Any]] = []

    for stop in trip_result.stop_arrivals:
        sla = sla_lookup.get(stop.stop_id)
        if sla is None:
            continue

        if isinstance(sla, dict):
            start_min = float(sla.get("start_time", 0))
            end_min = float(sla.get("end_time", 1439))
        else:
            start_min, end_min = float(sla[0]), float(sla[1])

        arr_time = stop.arrival_time_min

        # Hard SLA check: arrival must not exceed window end time (+ grace period)
        if arr_time > end_min + grace_period_min:
            lateness = arr_time - end_min
            violations.append({
                "stop_id": stop.stop_id,
                "arrival_time_min": arr_time,
                "sla_window": (start_min, end_min),
                "lateness_min": lateness,
                "type": "late_violation",
            })
        elif arr_time < start_min - grace_period_min:
            earliness = start_min - arr_time
            violations.append({
                "stop_id": stop.stop_id,
                "arrival_time_min": arr_time,
                "sla_window": (start_min, end_min),
                "earliness_min": earliness,
                "type": "early_arrival",
            })

    # Strict feasibility: only late arrivals make a route infeasible (early arrivals wait at stop)
    late_violations = [v for v in violations if v["type"] == "late_violation"]
    is_feasible = len(late_violations) == 0

    return is_feasible, violations


def calculate_qpso_fitness(
    simulated_routes: dict[str, list[TripArrivalResult]],
    sla_lookup: dict[str, tuple[int, int] | dict[str, int]],
    preset: str | CostWeights = "balanced",
    lateness_penalty_weight: float = 5.0,
) -> dict[str, Any]:
    """
    Compute multi-vehicle continuous timing fitness:
      f_QPSO = total_duration_min + (w4 * total_sla_lateness_penalty)

    Args:
        simulated_routes: Output of simulate_fleet_arrivals().
        sla_lookup: Mapping stop_id -> SLA window.
        preset: Optimization preset name or CostWeights instance.
        lateness_penalty_weight: Scale for late arrival minutes.

    Returns:
        Dict with 'fitness', 'total_duration_min', 'sla_penalty', and 'w4_sla'.
    """
    weights = get_preset_weights(preset) if isinstance(preset, str) else preset
    w4_sla = weights.w_sla

    total_duration = 0.0
    total_sla_penalty = 0.0
    total_violations_count = 0

    for _v_id, trips in simulated_routes.items():
        for trip in trips:
            total_duration += trip.total_duration_min
            _is_feas, violations = check_trip_sla_feasibility(trip, sla_lookup)
            for v in violations:
                if v["type"] == "late_violation":
                    lateness = v["lateness_min"]
                    # Quadratic lateness penalty for steep gradients
                    total_sla_penalty += lateness_penalty_weight * (lateness ** 2)
                    total_violations_count += 1
                elif v["type"] == "early_arrival":
                    # Mild linear waiting penalty (0.1x)
                    total_sla_penalty += 0.1 * v["earliness_min"]

    # Total QPSO fitness (minimization objective)
    f_qpso = total_duration + (w4_sla * total_sla_penalty)

    return {
        "fitness": float(f_qpso),
        "total_duration_min": total_duration,
        "sla_penalty": total_sla_penalty,
        "w4_sla": w4_sla,
        "violations_count": total_violations_count,
    }
