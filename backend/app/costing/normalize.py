"""
backend/app/costing/normalize.py — Milestone 2.1

Layer 2 (Normalization Layer) of the cost function architecture.
Transforms dimensional quantities (km, minutes, congestion ratio, penalties)
into dimensionless ratios relative to a Dijkstra-baseline reference,
ensuring unit-safe weighted scoring per spec §3b.
"""

from __future__ import annotations

import math


def normalize(value: float, reference: float, eps: float = 1e-6) -> float:
    """
    Normalize a metric relative to its baseline reference.

    Args:
        value: The observed metric value (e.g. actual route distance in km, or actual time in min).
        reference: The uncongested / baseline reference value.
        eps: Minimum positive denominator guard.

    Returns:
        Dimensionless normalized ratio (e.g. 1.0 = exactly on baseline, 1.25 = 25% over baseline).

    Raises:
        ValueError: If reference is non-positive or non-finite, or if value is non-finite.
    """
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"value must be a non-negative finite float, got {value}")
    if not math.isfinite(reference) or reference <= 0:
        raise ValueError(f"reference must be a positive finite float (> 0), got {reference}")

    denom = max(reference, eps)
    return float(value / denom)


def compute_route_baseline(
    baseline_distance_km: float,
    baseline_time_min: float,
    baseline_congestion_ratio: float = 1.0,
) -> dict[str, float]:
    """
    Package Dijkstra uncongested route metrics as normalization references.

    Args:
        baseline_distance_km: Uncongested shortest-path distance (km).
        baseline_time_min: Uncongested shortest-path travel time (min).
        baseline_congestion_ratio: Baseline congestion multiplier (default: 1.0).

    Returns:
        Dict of baseline reference values.
    """
    if baseline_distance_km <= 0 or baseline_time_min <= 0:
        raise ValueError("Baseline distance and time must be positive numbers.")

    return {
        "ref_distance_km": float(baseline_distance_km),
        "ref_time_min": float(baseline_time_min),
        "ref_congestion_ratio": float(baseline_congestion_ratio),
    }
