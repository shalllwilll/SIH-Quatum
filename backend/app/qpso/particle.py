"""
backend/app/qpso/particle.py — Milestone 4.1 (Optimized with NumPy vectorization)

Quantum-behaved Particle Swarm Optimization (QPSO) particle encoding
and delta-potential well position update rule per spec §3d.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


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
        pos_arr = np.nan_to_num(np.array(self.position, dtype=np.float64), nan=min_bound, posinf=max_bound, neginf=min_bound)
        np.clip(pos_arr, min_bound, max_bound, out=pos_arr)
        self.position = pos_arr.tolist()

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
        Quantum delta-potential well position update rule (Vectorized with NumPy):
          p_{d} = phi_{d} * pbest_{d} + (1 - phi_{d}) * gbest_{d}
          x_{d} = p_{d} +/- beta * |mbest_{d} - x_{d}| * ln(1 / u_{d})

        Args:
            gbest_position: Global best position vector across swarm.
            mbest_position: Mean-best position vector across all particles' pbests.
            beta: Contraction-expansion coefficient (typically in [0.5, 1.0]).
            seed: Optional random seed.
        """
        dim = len(self.position)
        if dim == 0:
            return

        rng = np.random.default_rng(seed)
        pbest_arr = np.array(self.pbest_position, dtype=np.float64)
        gbest_arr = np.array(gbest_position, dtype=np.float64)
        mbest_arr = np.array(mbest_position, dtype=np.float64)
        pos_arr = np.array(self.position, dtype=np.float64)

        # Vectorized stochastic attractor
        phi = rng.random(size=dim)
        p_d = (phi * pbest_arr) + ((1.0 - phi) * gbest_arr)

        u = np.clip(rng.random(size=dim), 1e-8, 1.0 - 1e-8)
        quantum_step = beta * np.abs(mbest_arr - pos_arr) * np.log(1.0 / u)

        # Vectorized random sign +/-
        signs = np.where(rng.random(size=dim) < 0.5, 1.0, -1.0)
        new_pos = p_d + (signs * quantum_step)

        min_bound, max_bound = self.bounds
        np.clip(new_pos, min_bound, max_bound, out=new_pos)
        self.position = new_pos.tolist()


def compute_mbest(particles: list[QPSOParticle]) -> list[float]:
    """Compute mean-best position vector across all particles in the swarm using NumPy."""
    if not particles:
        return []

    pbests = np.array([p.pbest_position for p in particles], dtype=np.float64)
    return np.mean(pbests, axis=0).tolist()
