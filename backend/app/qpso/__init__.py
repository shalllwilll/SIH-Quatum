"""
QPSO package — Quantum Particle Swarm Optimization (Milestones 4.1–4.2).
Continuous layer for departure timing and hard SLA constraint optimization.
"""

from app.qpso.arrival_simulator import (
    StopArrival,
    TripArrivalResult,
    simulate_fleet_arrivals,
    simulate_trip_arrivals,
)
from app.qpso.fitness import (
    calculate_qpso_fitness,
    check_trip_sla_feasibility,
)
from app.qpso.particle import QPSOParticle, compute_mbest
from app.qpso.run_qpso import QPSOResult, run_qpso

__all__ = [
    "QPSOParticle",
    "QPSOResult",
    "StopArrival",
    "TripArrivalResult",
    "calculate_qpso_fitness",
    "check_trip_sla_feasibility",
    "compute_mbest",
    "run_qpso",
    "simulate_fleet_arrivals",
    "simulate_trip_arrivals",
]
