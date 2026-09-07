"""
backend/tests/test_qga_run.py — Milestone 3.3 Test Suite

Test Cases:
  TC-3.3-01: GA improves fitness over generations (monotonic non-increasing with elitism)
  TC-3.3-02: GA converges on trivial 2-stop case
  TC-3.3-03: Order crossover preserves permutation validity
  TC-3.3-04: Mutation preserves permutation validity
  TC-3.3-05: Degenerate population handled gracefully (negative test)
  TC-3.3-06: Plateau termination condition triggers before max generations
  TC-3.3-07: Full cluster optimization run completes with valid routes
"""

import math

from app.qga.chromosome import (
    generate_random_chromosome,
    validate_chromosome,
)
from app.qga.operators import mutate_chromosome, order_crossover
from app.qga.run_qga import QGAResult, run_qga


def test_tc_3_3_01_monotonic_fitness_improvement():
    """TC-3.3-01: Best fitness is non-increasing across generations due to elitism."""
    stops = [f"P{i}" for i in range(1, 9)]
    res = run_qga(
        stops=stops,
        pop_size=20,
        max_generations=25,
        plateau_generations=0,
        seed=42,
    )

    assert isinstance(res, QGAResult)
    assert len(res.fitness_history) > 1

    # Check best fitness at each step is non-increasing
    for i in range(1, len(res.fitness_history)):
        prev_best = res.fitness_history[i - 1]["best_fitness"]
        curr_best = res.fitness_history[i]["best_fitness"]
        assert curr_best <= prev_best + 1e-6, (
            f"Fitness increased at gen {i}: {curr_best} > {prev_best}"
        )


def test_tc_3_3_02_trivial_convergence():
    """TC-3.3-02: QGA finds optimal ordering on 2-stop case."""
    # Distance: WH -> P1 -> P2 -> WH = 1 + 1 + 2 = 4
    # Distance: WH -> P2 -> P1 -> WH = 10 + 1 + 10 = 21
    distance_lookup = {
        ("WH-1", "P1"): 1.0,
        ("P1", "P2"): 1.0,
        ("P2", "WH-1"): 2.0,
        ("WH-1", "P2"): 10.0,
        ("P2", "P1"): 1.0,
        ("P1", "WH-1"): 10.0,
    }

    res = run_qga(
        stops=["P1", "P2"],
        distance_lookup=distance_lookup,
        vehicles=["VEH-1"],
        warehouse_id="WH-1",
        pop_size=10,
        max_generations=15,
        seed=42,
    )

    assert res.best_chromosome.stops() == ["P1", "P2"]


def test_tc_3_3_03_crossover_validity():
    """TC-3.3-03: Order crossover produces valid offspring without missing/duplicate stops."""
    stops = [f"P{i}" for i in range(1, 11)]
    p1 = generate_random_chromosome(stops, ["V1", "V2"], seed=10)
    p2 = generate_random_chromosome(stops, ["V1", "V2"], seed=20)

    for s in range(10):
        child = order_crossover(p1, p2, seed=s)
        is_valid, err = validate_chromosome(child, expected_stops=stops)
        assert is_valid, f"Crossover produced invalid child: {err}"


def test_tc_3_3_04_mutation_validity():
    """TC-3.3-04: Mutation produces valid chromosome without missing/duplicate stops."""
    stops = [f"P{i}" for i in range(1, 11)]
    parent = generate_random_chromosome(stops, ["V1", "V2"], seed=42)

    for s in range(10):
        mutated = mutate_chromosome(parent, mutation_rate=1.0, seed=s)
        is_valid, err = validate_chromosome(mutated, expected_stops=stops)
        assert is_valid, f"Mutation produced invalid child: {err}"


def test_tc_3_3_05_degenerate_population_handled():
    """TC-3.3-05 (Negative): Small/degenerate population sizes are handled gracefully."""
    stops = ["P1", "P2", "P3"]
    # pop_size = 1 is clamped to minimum 2
    res = run_qga(stops=stops, pop_size=1, max_generations=5, seed=42)
    assert res.generations_completed >= 1
    assert math.isfinite(res.best_fitness)


def test_tc_3_3_06_plateau_termination():
    """TC-3.3-06: Plateau termination triggers early exit when fitness stagnates."""
    stops = ["P1", "P2", "P3"]
    res = run_qga(
        stops=stops,
        pop_size=15,
        max_generations=100,
        plateau_generations=5,
        seed=42,
    )

    # Should terminate well before 100 generations
    assert res.generations_completed < 100
    assert res.converged


def test_tc_3_3_07_full_cluster_run():
    """TC-3.3-07 (Integration): Realistic 20-stop cluster completes under budget with valid routes."""
    stops = [f"PAR-PUNE-{i:04d}" for i in range(1, 21)]
    vehicles = ["VEH-001", "VEH-002", "VEH-003"]
    stop_weights = {s: 4.5 for s in stops}

    res = run_qga(
        stops=stops,
        stop_weights_kg=stop_weights,
        vehicles=vehicles,
        warehouse_id="WH-PUNE-001",
        pop_size=25,
        max_generations=30,
        seed=42,
    )

    assert isinstance(res, QGAResult)
    assert res.execution_time_ms > 0.0
    assert len(res.decoded_routes) > 0

    # Verify all 20 stops are routed across vehicles
    all_routed_stops = []
    for trips in res.decoded_routes.values():
        for trip in trips:
            all_routed_stops.extend(trip["stops"])

    assert sorted(all_routed_stops) == sorted(stops)
