"""
backend/app/qga/qubit_encoding.py — Milestone 3.3 (Optimized with NumPy vectorization)

Quantum-inspired qubit representation and rotation-gate evolution operators
for discrete combinatorial route optimization per spec §3d.

A quantum chromosome maintains probability amplitude angles theta_i in [0, pi/2]
for each stop decision. A quantum rotation gate updates theta_i toward the best-known
chromosome in each generation using vectorized NumPy operations.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import numpy as np

from app.qga.chromosome import (
    BreakGene,
    Chromosome,
    Gene,
    StopGene,
)


@dataclass
class QubitChromosome:
    """
    Quantum-inspired chromosome where each stop index has a probability angle theta.
    Amplitudes: alpha = cos(theta), beta = sin(theta).
    Probability of bit 1 = |beta|^2 = sin^2(theta).
    """
    stop_ids: list[str]
    vehicles: list[str]
    warehouse_id: str
    thetas: list[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.thetas and self.stop_ids:
            # Initialize to equal superposition (theta = pi/4 -> |alpha|^2 = |beta|^2 = 0.5)
            self.thetas = [math.pi / 4.0 for _ in range(len(self.stop_ids))]

    def observe(self, seed: int | None = None) -> Chromosome:
        """
        Collapse / observe quantum state to produce a classical Chromosome.

        Each stop's priority score is sampled from its probability distribution.
        Stops are ordered by priority score and partitioned among vehicles.
        Vectorized with NumPy for maximum performance.
        """
        n = len(self.stop_ids)
        if n == 0:
            return Chromosome(genes=[])

        rng = random.Random(seed)
        theta_arr = np.array(self.thetas, dtype=np.float64)

        # Vectorized probability amplitude & deterministic perturbation
        beta_sq = np.sin(theta_arr) ** 2
        scores = [float(beta_sq[i]) + (rng.uniform(-0.1, 0.1) * 0.2) for i in range(n)]

        # Sort indices by descending priority score
        sorted_indices = sorted(range(n), key=lambda i: scores[i], reverse=True)
        ordered_stops = [self.stop_ids[idx] for idx in sorted_indices]

        # Interleave breaks
        breaks = [
            BreakGene(vehicle_id=v, trip_number=1, warehouse_id=self.warehouse_id)
            for v in self.vehicles
        ]
        if not breaks:
            breaks = [BreakGene(vehicle_id="VEH-001", trip_number=1, warehouse_id=self.warehouse_id)]

        n_breaks = len(breaks)
        split_points = [int(i * n / n_breaks) for i in range(1, n_breaks)]

        genes: list[Gene] = []
        prev_idx = 0
        for b_idx, b_gene in enumerate(breaks):
            genes.append(b_gene)
            end_idx = split_points[b_idx] if b_idx < len(split_points) else n
            for s in ordered_stops[prev_idx:end_idx]:
                genes.append(StopGene(stop_id=s, warehouse_id=b_gene.warehouse_id))
            prev_idx = end_idx

        return Chromosome(genes=genes)

    def rotate_toward_best(
        self,
        current_chromosome: Chromosome,
        best_chromosome: Chromosome,
        step_size: float = 0.05 * math.pi,
    ) -> None:
        """
        Apply quantum rotation gate U(delta_theta) to shift amplitude angles
        toward the best observed chromosome.

        Rotation rule (Vectorized with NumPy):
          theta_new = theta_old + sign(target - current) * step_size
          bounded within [0.01 * pi, 0.49 * pi] to prevent premature stagnation.
        """
        best_stops = best_chromosome.stops()
        curr_stops = current_chromosome.stops()

        best_pos = {s: idx for idx, s in enumerate(best_stops)}
        curr_pos = {s: idx for idx, s in enumerate(curr_stops)}

        n = len(self.stop_ids)
        if n == 0:
            return

        deltas = np.zeros(n, dtype=np.float64)
        for i, stop_id in enumerate(self.stop_ids):
            target_idx = best_pos.get(stop_id, i)
            actual_idx = curr_pos.get(stop_id, i)
            if target_idx < actual_idx:
                deltas[i] = step_size
            elif target_idx > actual_idx:
                deltas[i] = -step_size

        theta_arr = np.array(self.thetas, dtype=np.float64) + deltas
        # Vectorized bounding in [0.01*pi, 0.49*pi]
        np.clip(theta_arr, 0.01 * np.pi, 0.49 * np.pi, out=theta_arr)
        self.thetas = theta_arr.tolist()
