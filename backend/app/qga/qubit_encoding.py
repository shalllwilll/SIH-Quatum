"""
backend/app/qga/qubit_encoding.py — Milestone 3.3

Quantum-inspired qubit representation and rotation-gate evolution operators
for discrete combinatorial route optimization per spec §3d.

A quantum chromosome maintains probability amplitude angles theta_i in [0, pi/2]
for each stop decision. A quantum rotation gate updates theta_i toward the best-known
chromosome in each generation.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

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
        """
        rng = random.Random(seed)
        n = len(self.stop_ids)
        if n == 0:
            return Chromosome(genes=[])

        # Priority sampling using beta^2 (probability of selection) + stochastic perturbation
        scores = []
        for i in range(n):
            theta = self.thetas[i]
            beta_sq = math.sin(theta) ** 2
            # Sample priority score
            score = beta_sq + (rng.uniform(-0.1, 0.1) * 0.2)
            scores.append((score, self.stop_ids[i]))

        # Sort stops in descending order of priority
        scores.sort(key=lambda x: x[0], reverse=True)
        ordered_stops = [s[1] for s in scores]

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

        Rotation rule:
          theta_new = theta_old + sign(target - current) * step_size
          bounded within [0.01 * pi, 0.49 * pi] to prevent premature stagnation.
        """
        best_stops = best_chromosome.stops()
        curr_stops = current_chromosome.stops()

        # Map stop positions in best chromosome
        best_pos = {s: idx for idx, s in enumerate(best_stops)}
        curr_pos = {s: idx for idx, s in enumerate(curr_stops)}

        for i, stop_id in enumerate(self.stop_ids):
            target_idx = best_pos.get(stop_id, i)
            actual_idx = curr_pos.get(stop_id, i)

            # If target index is earlier, increase priority angle theta
            if target_idx < actual_idx:
                delta = step_size
            elif target_idx > actual_idx:
                delta = -step_size
            else:
                delta = 0.0

            new_theta = self.thetas[i] + delta
            # Clamp within [0.01*pi, 0.49*pi]
            self.thetas[i] = max(0.01 * math.pi, min(0.49 * math.pi, new_theta))
