"""
backend/app/qga/run_qga.py — Milestone 3.3

Orchestrates the complete Quantum Genetic Algorithm (QGA) optimization loop
for a single cluster of delivery stops per spec §3d.
"""

from __future__ import annotations

import logging
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any

from app.qga.chromosome import Chromosome, validate_chromosome
from app.qga.decoder import decode_chromosome
from app.qga.fitness import calculate_qga_fitness
from app.qga.operators import mutate_chromosome, order_crossover, tournament_selection
from app.qga.qubit_encoding import QubitChromosome

log = logging.getLogger(__name__)


@dataclass
class QGAResult:
    """Result of a single-cluster QGA optimization run."""
    best_chromosome: Chromosome
    best_fitness: float
    decoded_routes: dict[str, list[dict[str, Any]]]
    fitness_history: list[dict[str, float]] = field(default_factory=list)
    generations_completed: int = 0
    converged: bool = False
    execution_time_ms: float = 0.0


def run_qga(
    stops: list[str],
    stop_weights_kg: dict[str, float] | None = None,
    distance_lookup: dict[tuple[str, str], float] | None = None,
    vehicles: list[str] | None = None,
    warehouse_id: str = "WH-PUNE-001",
    pop_size: int = 30,
    max_generations: int = 50,
    elitism_count: int = 2,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.2,
    rotation_step_size: float = 0.05 * math.pi,
    plateau_generations: int = 15,
    preset: str = "balanced",
    seed: int | None = 42,
) -> QGAResult:
    """
    Run the Quantum Genetic Algorithm loop on a single cluster of stops.

    Args:
        stops: List of stop IDs in this cluster.
        stop_weights_kg: Mapping stop_id -> weight in kg.
        distance_lookup: Precomputed pairwise distance matrix.
        vehicles: Available vehicle IDs for this cluster.
        warehouse_id: Dispatch warehouse ID.
        pop_size: Population size (enforces minimum of 2).
        max_generations: Maximum iteration count.
        elitism_count: Number of best individuals preserved unchanged.
        crossover_rate: Probability of crossover between parents.
        mutation_rate: Probability of mutation per offspring.
        rotation_step_size: Angular step size for quantum rotation gate.
        plateau_generations: Early termination if no improvement for N gens.
        preset: Session optimization preset (e.g. 'balanced').
        seed: Random seed for deterministic reproducibility.

    Returns:
        QGAResult dataclass containing best solution, decoded routes, and history.
    """
    t0 = time.perf_counter()
    rng = random.Random(seed)

    weights_kg = stop_weights_kg or {s: 5.0 for s in stops}
    veh_list = vehicles or ["VEH-001"]

    if not stops:
        empty_chrom = Chromosome(genes=[])
        return QGAResult(
            best_chromosome=empty_chrom,
            best_fitness=0.0,
            decoded_routes={},
            fitness_history=[],
            generations_completed=0,
            converged=True,
            execution_time_ms=0.0,
        )

    # Degenerate case: Single stop
    if len(stops) == 1:
        single_chrom = QubitChromosome(
            stop_ids=stops,
            vehicles=veh_list,
            warehouse_id=warehouse_id,
        ).observe(seed=seed)
        decoded = decode_chromosome(single_chrom)
        fit_eval = calculate_qga_fitness(decoded, weights_kg, distance_lookup, preset=preset)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return QGAResult(
            best_chromosome=single_chrom,
            best_fitness=fit_eval["fitness"],
            decoded_routes=decoded,
            fitness_history=[{"gen": 0, "best_fitness": fit_eval["fitness"], "avg_fitness": fit_eval["fitness"]}],
            generations_completed=1,
            converged=True,
            execution_time_ms=elapsed_ms,
        )

    # Enforce minimum population size of 2
    pop_size = max(2, pop_size)
    elitism_count = max(1, min(elitism_count, pop_size // 2))

    # 1. Initialize Quantum Population
    q_population: list[QubitChromosome] = [
        QubitChromosome(
            stop_ids=stops,
            vehicles=veh_list,
            warehouse_id=warehouse_id,
        )
        for _ in range(pop_size)
    ]

    # Initial classical observation
    population: list[Chromosome] = [
        q_ind.observe(seed=rng.randint(0, 1000000))
        for q_ind in q_population
    ]

    def eval_pop(pop: list[Chromosome]) -> list[float]:
        fits = []
        for ind in pop:
            dec = decode_chromosome(ind)
            res = calculate_qga_fitness(dec, weights_kg, distance_lookup, preset=preset)
            fits.append(res["fitness"])
        return fits

    fitnesses = eval_pop(population)

    # Track best-so-far
    best_idx = min(range(pop_size), key=lambda i: fitnesses[i])
    best_chrom = population[best_idx].copy()
    best_fitness = fitnesses[best_idx]

    fitness_history = [
        {
            "gen": 0,
            "best_fitness": best_fitness,
            "avg_fitness": sum(fitnesses) / len(fitnesses),
        }
    ]

    gens_without_improvement = 0
    converged = False
    gen = 0

    # Main Evolutionary Loop
    for gen in range(1, max_generations + 1):
        # 2. Quantum Rotation-Gate Phase
        for i in range(pop_size):
            q_population[i].rotate_toward_best(
                current_chromosome=population[i],
                best_chromosome=best_chrom,
                step_size=rotation_step_size,
            )

        # 3. Collapse / Observation
        observed_pop = [
            q_population[i].observe(seed=rng.randint(0, 1000000))
            for i in range(pop_size)
        ]

        # 4. Selection, Crossover & Mutation
        offspring: list[Chromosome] = []
        while len(offspring) < pop_size - elitism_count:
            p1 = tournament_selection(observed_pop, fitnesses, tournament_size=3, seed=rng.randint(0, 1000000))
            p2 = tournament_selection(observed_pop, fitnesses, tournament_size=3, seed=rng.randint(0, 1000000))

            if rng.random() < crossover_rate:
                child = order_crossover(p1, p2, seed=rng.randint(0, 1000000))
            else:
                child = p1.copy()

            child = mutate_chromosome(child, mutation_rate=mutation_rate, seed=rng.randint(0, 1000000))
            offspring.append(child)

        # 5. Elitism: preserve best individuals
        sorted_indices = sorted(range(pop_size), key=lambda i: fitnesses[i])
        elites = [population[i].copy() for i in sorted_indices[:elitism_count]]

        population = elites + offspring
        fitnesses = eval_pop(population)

        # 6. Update best-so-far
        gen_best_idx = min(range(pop_size), key=lambda i: fitnesses[i])
        gen_best_fit = fitnesses[gen_best_idx]

        if gen_best_fit < best_fitness:
            best_fitness = gen_best_fit
            best_chrom = population[gen_best_idx].copy()
            gens_without_improvement = 0
        else:
            gens_without_improvement += 1

        fitness_history.append(
            {
                "gen": gen,
                "best_fitness": best_fitness,
                "avg_fitness": sum(fitnesses) / len(fitnesses),
            }
        )

        # 7. Plateau Termination Check
        if plateau_generations > 0 and gens_without_improvement >= plateau_generations:
            log.info("QGA converged early at generation %d (plateau detected)", gen)
            converged = True
            break

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    decoded_best = decode_chromosome(best_chrom)

    # Sanity validation
    is_valid, err = validate_chromosome(best_chrom, expected_stops=stops)
    if not is_valid:
        log.error("QGA produced invalid chromosome: %s", err)

    return QGAResult(
        best_chromosome=best_chrom,
        best_fitness=best_fitness,
        decoded_routes=decoded_best,
        fitness_history=fitness_history,
        generations_completed=gen,
        converged=converged or (gen == max_generations),
        execution_time_ms=elapsed_ms,
    )
