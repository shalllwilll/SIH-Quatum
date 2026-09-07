"""
backend/tests/test_qga_fitness.py — Milestone 3.2 Test Suite

Test Cases:
  TC-3.2-01: Under-capacity route has zero capacity penalty
  TC-3.2-02: Over-capacity route is penalized smoothly without rejection
  TC-3.2-03: Capacity penalty scales smoothly with overload severity
  TC-3.2-04: High load imbalance across fleet receives positive penalty
  TC-3.2-05: Empty route handles division-by-zero safely (negative test)
  TC-3.2-06: Preset w1 weight scales distance component proportionally
"""

import math

import pytest

from app.qga.fitness import (
    calculate_qga_fitness,
    capacity_penalty,
    load_imbalance_penalty,
)


def test_tc_3_2_01_under_capacity_zero_penalty():
    """TC-3.2-01: Vehicle with load <= capacity incurs zero capacity penalty."""
    assert capacity_penalty(vehicle_load_kg=80.0, capacity_kg=100.0) == 0.0
    assert capacity_penalty(vehicle_load_kg=100.0, capacity_kg=100.0) == 0.0


def test_tc_3_2_02_over_capacity_penalized():
    """TC-3.2-02: Over-capacity route returns finite penalty without crashing."""
    pen = capacity_penalty(vehicle_load_kg=120.0, capacity_kg=100.0)
    assert pen > 0.0
    assert math.isfinite(pen)


def test_tc_3_2_03_penalty_scaling_with_severity():
    """TC-3.2-03: Penalty for 50kg overload is significantly larger than for 5kg overload."""
    pen_5kg = capacity_penalty(vehicle_load_kg=105.0, capacity_kg=100.0)
    pen_50kg = capacity_penalty(vehicle_load_kg=150.0, capacity_kg=100.0)

    assert pen_50kg > pen_5kg
    # Quadratic growth: (50/100)^2 / (5/100)^2 = 100x ratio
    assert pen_50kg == pytest.approx(pen_5kg * 100.0)


def test_tc_3_2_04_load_imbalance_penalized():
    """TC-3.2-04: Fleet with uneven load distribution receives higher penalty than balanced fleet."""
    # Balanced fleet: two vehicles with 50kg each
    imbal_balanced = load_imbalance_penalty([50.0, 50.0])
    assert imbal_balanced == pytest.approx(0.0)

    # Imbalanced fleet: 90kg on one, 10kg on other (same total load = 100kg)
    imbal_skewed = load_imbalance_penalty([90.0, 10.0])
    assert imbal_skewed > 0.0

    # Test via calculate_qga_fitness
    stop_weights = {"P1": 50.0, "P2": 50.0}
    balanced_routes = {
        "VEH-001": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": ["P1"]}],
        "VEH-002": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": ["P2"]}],
    }
    imbalanced_routes = {
        "VEH-001": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": ["P1", "P2"]}],
        "VEH-002": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": []}],
    }

    res_bal = calculate_qga_fitness(balanced_routes, stop_weights, default_capacity_kg=100.0)
    res_imbal = calculate_qga_fitness(imbalanced_routes, stop_weights, default_capacity_kg=100.0)

    assert res_imbal["imbalance_penalty"] > res_bal["imbalance_penalty"]


def test_tc_3_2_05_empty_route_handled():
    """TC-3.2-05 (Negative): Empty routes produce finite 0-safe fitness."""
    empty_routes = {
        "VEH-001": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": []}],
    }
    res = calculate_qga_fitness(empty_routes, stop_weights_kg={})
    assert math.isfinite(res["fitness"])
    assert res["total_distance_km"] == 0.0
    assert res["capacity_penalty"] == 0.0


def test_tc_3_2_06_preset_weight_applied():
    """TC-3.2-06: Preset w1 weights scale distance component proportionally."""
    routes = {
        "VEH-001": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": ["P1"]}],
    }
    stop_weights = {"P1": 10.0}

    # Minimize Distance preset has w1 = 0.50
    res_dist = calculate_qga_fitness(routes, stop_weights, preset="minimize_distance")
    # Prioritize SLA preset has w1 = 0.15
    res_sla = calculate_qga_fitness(routes, stop_weights, preset="prioritize_sla")

    assert res_dist["w1_distance"] == pytest.approx(0.50)
    assert res_sla["w1_distance"] == pytest.approx(0.15)
    assert res_dist["fitness"] > res_sla["fitness"]
