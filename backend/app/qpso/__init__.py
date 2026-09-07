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
from app.qpso.particle import QPSOParticle, compute_mbest

__all__ = [
    "QPSOParticle",
    "StopArrival",
    "TripArrivalResult",
    "compute_mbest",
    "simulate_fleet_arrivals",
    "simulate_trip_arrivals",
]
