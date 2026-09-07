"""
backend/app/qga/fitness.py — Milestone 3.2

QGA multi-objective combinatorial fitness evaluation per spec §3d:
  f_QGA = w1 * norm_distance + penalty(capacity violations) + penalty(load imbalance)

Features:
- Smooth continuous capacity penalty (quadratic beyond vehicle capacity per spec §2a)
- Fleet load variance penalty for load balancing
- Fixed preset weighting (w1 from session preset) ensuring circularity-free optimization
"""

from __future__ import annotations

from typing import Any

from app.costing.presets import CostWeights, get_preset_weights


def capacity_penalty(
    vehicle_load_kg: float,
    capacity_kg: float,
    penalty_scale: float = 2.0,
) -> float:
    """
    Compute smooth continuous penalty for vehicle capacity violations.

    Per spec §2a: mild overloads are penalized smoothly (not rejected outright),
    allowing trade-offs between minor capacity overflow and significant distance savings.

    Args:
        vehicle_load_kg: Total weight assigned to vehicle in kg.
        capacity_kg: Maximum nominal vehicle capacity in kg.
        penalty_scale: Scaling factor for capacity penalty.

    Returns:
        Smooth dimensionless penalty value (>= 0.0).
    """
    if vehicle_load_kg <= capacity_kg:
        return 0.0

    overload_kg = vehicle_load_kg - capacity_kg
    # Dimensionless relative overload ratio, squared for smooth gradient
    relative_overload = overload_kg / max(capacity_kg, 1.0)
    return float(penalty_scale * (relative_overload ** 2))


def load_imbalance_penalty(
    vehicle_loads_kg: list[float],
    penalty_scale: float = 0.5,
) -> float:
    """
    Compute load imbalance penalty across fleet active vehicles.

    Penalizes high variance in cargo allocation to encourage even work distribution.

    Args:
        vehicle_loads_kg: List of total loads per active vehicle in kg.
        penalty_scale: Scaling factor for imbalance penalty.

    Returns:
        Dimensionless penalty value (>= 0.0).
    """
    if len(vehicle_loads_kg) <= 1:
        return 0.0

    mean_load = sum(vehicle_loads_kg) / len(vehicle_loads_kg)
    if mean_load <= 0.0:
        return 0.0

    # Relative coefficient of variation squared
    variance = sum((load - mean_load) ** 2 for load in vehicle_loads_kg) / len(vehicle_loads_kg)
    normalized_variance = variance / (mean_load ** 2)
    return float(penalty_scale * normalized_variance)


def calculate_qga_fitness(
    decoded_routes: dict[str, list[dict[str, Any]]],
    stop_weights_kg: dict[str, float],
    distance_lookup: dict[tuple[str, str], float] | None = None,
    default_capacity_kg: float = 100.0,
    preset: str | CostWeights = "balanced",
    reference_distance_km: float | None = None,
) -> dict[str, Any]:
    """
    Evaluate overall QGA fitness for a multi-vehicle multi-trip route schedule.

    Args:
        decoded_routes: Output of decode_chromosome(): {vehicle_id: [trip_dict, ...]}.
        stop_weights_kg: Mapping stop_id -> weight_kg.
        distance_lookup: Mapping (origin_id, dest_id) -> distance_km.
        default_capacity_kg: Nominal payload limit per vehicle.
        preset: Session preset name (e.g. 'balanced', 'minimize_distance') or CostWeights.
        reference_distance_km: Baseline reference distance for normalization.

    Returns:
        Dict with total 'fitness', 'distance_km', 'capacity_penalty', 'imbalance_penalty', etc.
    """
    weights = get_preset_weights(preset) if isinstance(preset, str) else preset
    w1_distance = weights.w_distance

    total_distance_km = 0.0
    vehicle_loads: dict[str, float] = {}

    for vehicle_id, trips in decoded_routes.items():
        v_total_load = 0.0
        for trip in trips:
            stops = trip.get("stops", [])
            warehouse_id = trip.get("warehouse_id", "WH-PUNE-001")

            # Accumulate payload weight
            trip_load = sum(stop_weights_kg.get(s, 5.0) for s in stops)
            v_total_load += trip_load

            # Accumulate route distance: Warehouse -> Stop1 -> Stop2 -> ... -> Warehouse
            if stops:
                prev_loc = warehouse_id
                for stop in stops:
                    dist = 1.0  # Default 1 km fallback if lookup is absent
                    if distance_lookup is not None:
                        dist = distance_lookup.get((prev_loc, stop), 1.0)
                    total_distance_km += dist
                    prev_loc = stop

                # Return leg to warehouse
                return_dist = 1.0
                if distance_lookup is not None:
                    return_dist = distance_lookup.get((prev_loc, warehouse_id), 1.0)
                total_distance_km += return_dist

        vehicle_loads[vehicle_id] = v_total_load

    # 1. Capacity penalties (summed across all vehicles)
    total_cap_penalty = sum(
        capacity_penalty(load, default_capacity_kg)
        for load in vehicle_loads.values()
    )

    # 2. Fleet load imbalance penalty across all allocated vehicles
    all_loads = list(vehicle_loads.values())
    imbal_penalty = load_imbalance_penalty(all_loads)

    # 3. Distance term (normalized if reference provided, else raw)
    ref_dist = reference_distance_km if reference_distance_km and reference_distance_km > 0 else max(total_distance_km, 1.0)
    norm_distance = total_distance_km / ref_dist

    # Total QGA fitness (minimization objective)
    f_qga = (w1_distance * norm_distance) + total_cap_penalty + imbal_penalty

    return {
        "fitness": float(f_qga),
        "total_distance_km": total_distance_km,
        "norm_distance": norm_distance,
        "capacity_penalty": total_cap_penalty,
        "imbalance_penalty": imbal_penalty,
        "vehicle_loads_kg": vehicle_loads,
        "w1_distance": w1_distance,
    }
