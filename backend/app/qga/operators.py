"""
backend/app/qga/operators.py — Milestone 3.3

Genetic operators for grouped-permutation chromosomes:
- Order Crossover (OX) adapted for permutation chromosomes with break preservation
- Swap, Inversion, and Move mutation operators
- Tournament selection
- Elitism preservation
"""

from __future__ import annotations

import random

from app.qga.chromosome import (
    BreakGene,
    Chromosome,
    Gene,
    StopGene,
)


def order_crossover(parent1: Chromosome, parent2: Chromosome, seed: int | None = None) -> Chromosome:
    """
    Perform Order Crossover (OX) on the stops permutation of two parents,
    preserving vehicle and trip break structures.
    """
    rng = random.Random(seed)
    stops1 = parent1.stops()
    stops2 = parent2.stops()

    n = len(stops1)
    if n <= 1:
        return parent1.copy()

    # Choose two crossover points in stops
    pt1, pt2 = sorted(rng.sample(range(n), 2))

    # Segment from parent1
    child_stops: list[str | None] = [None] * n
    child_stops[pt1 : pt2 + 1] = stops1[pt1 : pt2 + 1]
    filled_set = set(child_stops[pt1 : pt2 + 1])

    # Fill remaining positions in circular order from parent2
    p2_remaining = [s for s in stops2[pt2 + 1 :] + stops2[: pt2 + 1] if s not in filled_set]
    fill_idx = (pt2 + 1) % n
    for s in p2_remaining:
        while child_stops[fill_idx] is not None:
            fill_idx = (fill_idx + 1) % n
        child_stops[fill_idx] = s

    # Reconstruct chromosome with parent1's break positions
    new_genes: list[Gene] = []
    stop_iter = iter([s for s in child_stops if s is not None])

    for gene in parent1.genes:
        if isinstance(gene, BreakGene):
            new_genes.append(gene)
        elif isinstance(gene, StopGene):
            s_id = next(stop_iter)
            new_genes.append(StopGene(stop_id=s_id, warehouse_id=gene.warehouse_id))

    return Chromosome(genes=new_genes)


def mutate_chromosome(
    chromosome: Chromosome,
    mutation_rate: float = 0.15,
    seed: int | None = None,
) -> Chromosome:
    """
    Apply permutation-safe mutation (swap or inversion) to stop genes.
    """
    rng = random.Random(seed)
    if rng.random() > mutation_rate:
        return chromosome.copy()

    genes = list(chromosome.genes)
    stop_indices = [i for i, g in enumerate(genes) if isinstance(g, StopGene)]

    if len(stop_indices) < 2:
        return chromosome.copy()

    mutation_type = rng.choice(["swap", "inversion"])

    if mutation_type == "swap":
        # Swap two random stops
        i1, i2 = rng.sample(stop_indices, 2)
        g1, g2 = genes[i1], genes[i2]
        genes[i1] = StopGene(stop_id=g2.stop_id, warehouse_id=g1.warehouse_id)
        genes[i2] = StopGene(stop_id=g1.stop_id, warehouse_id=g2.warehouse_id)
    elif mutation_type == "inversion":
        # Invert a subsegment of stops
        idx_a, idx_b = sorted(rng.sample(range(len(stop_indices)), 2))
        selected_indices = stop_indices[idx_a : idx_b + 1]
        stops_to_reverse = [genes[idx].stop_id for idx in selected_indices]
        stops_to_reverse.reverse()

        for slot_idx, reversed_stop_id in zip(selected_indices, stops_to_reverse, strict=True):
            genes[slot_idx] = StopGene(
                stop_id=reversed_stop_id,
                warehouse_id=genes[slot_idx].warehouse_id,
            )

    return Chromosome(genes=genes)


def tournament_selection(
    population: list[Chromosome],
    fitnesses: list[float],
    tournament_size: int = 3,
    seed: int | None = None,
) -> Chromosome:
    """
    Select one individual using tournament selection (minimization objective).
    """
    rng = random.Random(seed)
    n = len(population)
    k = min(tournament_size, n)
    indices = rng.sample(range(n), k)

    # Winner is individual with lowest fitness (minimization)
    best_idx = min(indices, key=lambda i: fitnesses[i])
    return population[best_idx]
