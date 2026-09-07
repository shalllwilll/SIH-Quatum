"""
backend/app/qpso/particle.py — Milestone 4.1

Quantum-behaved Particle Swarm Optimization (QPSO) particle encoding
and delta-potential well position update rule per spec §3d.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class QPSOParticle:
    """
    QPSO particle representing a continuous vector of departure-time offsets
    (one dimension per vehicle-trip) in minutes since midnight.
    """
    position: list[float]
    bounds: tuple[float, float] = (360.0, 1200.0)  # Default: 06:00 AM to 08:00 PM
    pbest_position: list[float] = field(default_factory=list)
    pbest_fitness: float = float("inf")

    def __post_init__(self):
        self.clamp_position()
        if not self.pbest_position:
            self.pbest_position = list(self.position)

    def clamp_position(self) -> None:
        """Enforce strict warehouse operating hour bounds on particle position."""
        min_bound, max_bound = self.bounds
        for d in range(len(self.position)):
            val = self.position[d]
            if not math.isfinite(val):
                self.position[d] = min_bound
            else:
                self.position[d] = max(min_bound, min(max_bound, val))

    def update_pbest(self, current_fitness: float) -> bool:
        """
        Update personal best if current fitness is strictly better (lower).

        Returns:
            bool: True if personal best was updated, False otherwise.
        """
        if current_fitness < self.pbest_fitness:
            self.pbest_fitness = current_fitness
            self.pbest_position = list(self.position)
            return True
        return False

    def update_quantum_position(
        self,
        gbest_position: list[float],
        mbest_position: list[float],
        beta: float = 0.75,
        seed: int | None = None,
    ) -> None:
        """
        Quantum delta-potential well position update rule:
          p_{d} = phi_{d} * pbest_{d} + (1 - phi_{d}) * gbest_{d}
          x_{d} = p_{d} +/- beta * |mbest_{d} - x_{d}| * ln(1 / u_{d})

        Args:
            gbest_position: Global best position vector across swarm.
            mbest_position: Mean-best position vector across all particles' pbests.
            beta: Contraction-expansion coefficient (typically in [0.5, 1.0]).
            seed: Optional random seed.
        """
        rng = random.Random(seed)
        dim = len(self.position)

        for d in range(dim):
            phi = rng.random()
            # Local stochastic attractor
            p_d = (phi * self.pbest_position[d]) + ((1.0 - phi) * gbest_position[d])

            u = max(1e-8, min(1.0 - 1e-8, rng.random()))
            quantum_step = beta * abs(mbest_position[d] - self.position[d]) * math.log(1.0 / u)

            # Random sign +/-
            sign = 1.0 if rng.random() < 0.5 else -1.0
            new_pos = p_d + (sign * quantum_step)

            self.position[d] = new_pos

        self.clamp_position()


def compute_mbest(particles: list[QPSOParticle]) -> list[float]:
    """Compute mean-best position vector across all particles in the swarm."""
    if not particles:
        return []

    dim = len(particles[0].position)
    mbest = [0.0] * dim

    for d in range(dim):
        mbest[d] = sum(p.pbest_position[d] for p in particles) / len(particles)

    return mbest
