"""
backend/app/costing/physics.py — Milestone 2.1

Layer 1 (Physics Layer) of the cost function architecture.
Computes actual edge travel time under congestion with swappable modes
(multiplicative vs additive) per spec §3b.
"""

from __future__ import annotations

import math
from enum import StrEnum


class CongestionMode(StrEnum):
    MULTIPLICATIVE = "multiplicative"
    ADDITIVE = "additive"


def edge_travel_time(
    base_time_min: float,
    congestion_value: float,
    mode: str | CongestionMode = CongestionMode.MULTIPLICATIVE,
) -> float:
    """
    Compute congested edge travel time in minutes.

    Args:
        base_time_min: Uncongested base travel time in minutes (must be >= 0).
        congestion_value: Congestion factor (ratio >= 1.0 for multiplicative,
                          or delay in minutes >= 0 for additive).
        mode: Congestion mode ("multiplicative" or "additive").

    Returns:
        Congested travel time in minutes (finite float >= 0).

    Raises:
        ValueError: If mode is not recognized, or if numeric inputs are invalid.
    """
    if not math.isfinite(base_time_min) or base_time_min < 0:
        raise ValueError(f"base_time_min must be a non-negative finite float, got {base_time_min}")
    if not math.isfinite(congestion_value) or congestion_value < 0:
        raise ValueError(f"congestion_value must be a non-negative finite float, got {congestion_value}")

    normalized_mode = str(mode).strip().lower()

    if normalized_mode == CongestionMode.MULTIPLICATIVE:
        travel_time = base_time_min * congestion_value
    elif normalized_mode == CongestionMode.ADDITIVE:
        travel_time = base_time_min + congestion_value
    else:
        raise ValueError(
            f"Unknown congestion mode: '{mode}'. Must be '{CongestionMode.MULTIPLICATIVE}' "
            f"or '{CongestionMode.ADDITIVE}'."
        )

    return max(0.0, float(travel_time))
