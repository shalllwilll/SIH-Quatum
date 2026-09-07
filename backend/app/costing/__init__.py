"""
Costing package — Milestone 2.1.
Three-layer cost function: Physics, Normalization, and Multi-Objective Fitness.
"""

from app.costing.fitness import calculate_fitness, evaluate_route_cost
from app.costing.normalize import compute_route_baseline, normalize
from app.costing.physics import CongestionMode, edge_travel_time
from app.costing.presets import (
    BALANCED,
    MINIMIZE_COST_FUEL,
    MINIMIZE_DISTANCE,
    PRESETS,
    PRIORITIZE_SLA,
    CostWeights,
    get_preset_weights,
)

__all__ = [
    "BALANCED",
    "MINIMIZE_COST_FUEL",
    "MINIMIZE_DISTANCE",
    "PRESETS",
    "PRIORITIZE_SLA",
    "CongestionMode",
    "CostWeights",
    "calculate_fitness",
    "compute_route_baseline",
    "edge_travel_time",
    "evaluate_route_cost",
    "get_preset_weights",
    "normalize",
]
