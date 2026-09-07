"""
backend/app/costing/fitness.py — Milestone 2.1

Layer 3 (Scoring Layer) of the cost function architecture.
Computes the multi-objective fitness score F per spec §3b:
  F = w1 * norm_distance + w2 * norm_time + w3 * norm_congestion_exposure + w4 * sla_soft_signal

All terms are normalized and dimensionless, making weights genuinely comparable
and independent of physical units (km, minutes, penalty counts).
"""

from __future__ import annotations

import math
from typing import Any

from app.costing.normalize import normalize
from app.costing.presets import CostWeights, get_preset_weights


def calculate_fitness(
    norm_distance: float,
    norm_time: float,
    norm_congestion: float,
    sla_soft_signal: float,
    weights: CostWeights | tuple[float, float, float, float],
) -> float:
    """
    Compute scalar fitness score F from normalized dimensionless components.

    Lower is better (minimization objective).

    Args:
        norm_distance: Normalized distance ratio (e.g. 1.0 = baseline).
        norm_time: Normalized travel time ratio (e.g. 1.0 = baseline).
        norm_congestion: Normalized congestion factor / exposure ratio.
        sla_soft_signal: Dimensionless soft signal for SLA proximity / minor violations (>= 0.0).
        weights: 4-tuple or CostWeights (w_dist, w_time, w_cong, w_sla) summing to 1.0.

    Returns:
        Scalar fitness value F (float >= 0.0).

    Raises:
        ValueError: If weights do not sum to 1.0 or if inputs are non-finite/negative.
    """
    for name, val in [
        ("norm_distance", norm_distance),
        ("norm_time", norm_time),
        ("norm_congestion", norm_congestion),
        ("sla_soft_signal", sla_soft_signal),
    ]:
        if not math.isfinite(val) or val < 0:
            raise ValueError(f"{name} must be a non-negative finite float, got {val}")

    if isinstance(weights, CostWeights):
        w1, w2, w3, w4 = weights.w_distance, weights.w_time, weights.w_congestion, weights.w_sla
    elif isinstance(weights, (tuple, list)) and len(weights) == 4:
        w1, w2, w3, w4 = float(weights[0]), float(weights[1]), float(weights[2]), float(weights[3])
    else:
        raise ValueError(f"weights must be a CostWeights instance or 4-tuple of floats, got {weights}")

    weight_sum = w1 + w2 + w3 + w4
    if not math.isclose(weight_sum, 1.0, rel_tol=1e-5):
        raise ValueError(f"Weights must sum to 1.0, but sum({w1}, {w2}, {w3}, {w4}) = {weight_sum}")

    fitness = (
        w1 * norm_distance
        + w2 * norm_time
        + w3 * norm_congestion
        + w4 * sla_soft_signal
    )
    return float(fitness)


def evaluate_route_cost(
    distance_km: float,
    time_min: float,
    congestion_ratio: float,
    sla_soft_signal: float,
    baseline: dict[str, float],
    preset: str | CostWeights = "balanced",
) -> dict[str, Any]:
    """
    End-to-end evaluation: normalize raw metrics against baseline references
    and compute fitness score with full component breakdown.

    Args:
        distance_km: Observed route distance in km.
        time_min: Observed route travel time in minutes.
        congestion_ratio: Average congestion factor on route (>= 1.0).
        sla_soft_signal: Dimensionless soft signal for SLA proximity.
        baseline: Dict containing 'ref_distance_km' and 'ref_time_min'.
        preset: Preset name string (e.g. 'balanced') or CostWeights instance.

    Returns:
        Dict containing total 'fitness' and component breakdown.
    """
    weights = get_preset_weights(preset) if isinstance(preset, str) else preset

    ref_dist = baseline["ref_distance_km"]
    ref_time = baseline["ref_time_min"]
    ref_cong = baseline.get("ref_congestion_ratio", 1.0)

    norm_dist = normalize(distance_km, ref_dist)
    norm_time = normalize(time_min, ref_time)
    norm_cong = normalize(congestion_ratio, ref_cong)

    fitness = calculate_fitness(
        norm_distance=norm_dist,
        norm_time=norm_time,
        norm_congestion=norm_cong,
        sla_soft_signal=sla_soft_signal,
        weights=weights,
    )

    return {
        "fitness": fitness,
        "norm_distance": norm_dist,
        "norm_time": norm_time,
        "norm_congestion": norm_cong,
        "sla_soft_signal": sla_soft_signal,
        "weights": weights.to_tuple() if isinstance(weights, CostWeights) else tuple(weights),
        "raw_distance_km": distance_km,
        "raw_time_min": time_min,
        "raw_congestion_ratio": congestion_ratio,
    }
