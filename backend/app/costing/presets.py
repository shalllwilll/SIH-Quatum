"""
backend/app/costing/presets.py — Milestone 2.1

Defines the 4 business-priority optimization weight presets from spec §9.
Each preset defines a 4-tuple of weights (w1_distance, w2_time, w3_congestion, w4_sla)
summing strictly to 1.0, ensuring genuine relative importance across objectives.
"""

from __future__ import annotations

import math
from typing import Final, NamedTuple


class CostWeights(NamedTuple):
    w_distance: float
    w_time: float
    w_congestion: float
    w_sla: float

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.w_distance, self.w_time, self.w_congestion, self.w_sla)


# ---------------------------------------------------------------------------
# Business Priority Presets (spec §9)
# Format: CostWeights(w_distance, w_time, w_congestion, w_sla)
# ---------------------------------------------------------------------------
MINIMIZE_DISTANCE: Final[CostWeights] = CostWeights(0.50, 0.20, 0.15, 0.15)
MINIMIZE_COST_FUEL: Final[CostWeights] = CostWeights(0.35, 0.15, 0.35, 0.15)
PRIORITIZE_SLA: Final[CostWeights] = CostWeights(0.15, 0.20, 0.15, 0.50)
BALANCED: Final[CostWeights] = CostWeights(0.25, 0.25, 0.25, 0.25)

PRESETS: Final[dict[str, CostWeights]] = {
    "minimize_distance": MINIMIZE_DISTANCE,
    "minimize_cost_fuel": MINIMIZE_COST_FUEL,
    "prioritize_sla": PRIORITIZE_SLA,
    "balanced": BALANCED,
}


def get_preset_weights(preset_name: str) -> CostWeights:
    """
    Retrieve weight preset by name.

    Args:
        preset_name: One of 'minimize_distance', 'minimize_cost_fuel', 'prioritize_sla', 'balanced'.

    Returns:
        CostWeights named tuple.

    Raises:
        KeyError: If preset_name is not found.
    """
    normalized_key = preset_name.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized_key not in PRESETS:
        raise KeyError(
            f"Unknown preset: '{preset_name}'. Valid presets are: {list(PRESETS.keys())}"
        )
    return PRESETS[normalized_key]


# ---------------------------------------------------------------------------
# Module validation: Assert all presets sum to 1.0 (tolerance 1e-6)
# ---------------------------------------------------------------------------
for _name, _w in PRESETS.items():
    _total = _w.w_distance + _w.w_time + _w.w_congestion + _w.w_sla
    assert math.isclose(_total, 1.0, rel_tol=1e-6), (
        f"Preset '{_name}' weights do not sum to 1.0: total={_total}"
    )
