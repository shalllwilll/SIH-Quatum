"""
backend/tests/test_costing.py — Milestone 2.1 Test Suite

Test Cases:
  TC-2.1-01: Multiplicative congestion calculation
  TC-2.1-02: Additive congestion calculation
  TC-2.1-03: Invalid congestion mode rejected with ValueError
  TC-2.1-04: Normalization scales correctly
  TC-2.1-05: Zero or negative reference value rejected gracefully
  TC-2.1-06: All 4 preset weights sum to 1.0
  TC-2.1-07: Fitness function unit-safety verification
  TC-2.1-08: End-to-end route cost evaluation
"""

import math

import pytest

from app.costing.fitness import calculate_fitness, evaluate_route_cost
from app.costing.normalize import compute_route_baseline, normalize
from app.costing.physics import CongestionMode, edge_travel_time
from app.costing.presets import (
    BALANCED,
    MINIMIZE_COST_FUEL,
    MINIMIZE_DISTANCE,
    PRESETS,
    PRIORITIZE_SLA,
    get_preset_weights,
)


def test_tc_2_1_01_multiplicative_congestion():
    """TC-2.1-01: Verify multiplicative congestion mode."""
    res = edge_travel_time(10.0, 1.4, "multiplicative")
    assert res == pytest.approx(14.0)

    res_enum = edge_travel_time(10.0, 1.4, CongestionMode.MULTIPLICATIVE)
    assert res_enum == pytest.approx(14.0)


def test_tc_2_1_02_additive_congestion():
    """TC-2.1-02: Verify additive congestion mode."""
    res = edge_travel_time(10.0, 8.0, "additive")
    assert res == pytest.approx(18.0)

    res_enum = edge_travel_time(10.0, 8.0, CongestionMode.ADDITIVE)
    assert res_enum == pytest.approx(18.0)


def test_tc_2_1_03_invalid_mode_rejected():
    """TC-2.1-03 (Negative): Verify invalid mode raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        edge_travel_time(10.0, 1.5, "unknown_mode")
    assert "Unknown congestion mode" in str(exc_info.value)


def test_tc_2_1_04_normalization_scales_correctly():
    """TC-2.1-04: Verify normalization ratio calculation."""
    res = normalize(20.0, reference=10.0)
    assert res == pytest.approx(2.0)

    # Identical value and baseline = 1.0
    assert normalize(15.5, reference=15.5) == pytest.approx(1.0)


def test_tc_2_1_05_zero_reference_handled():
    """TC-2.1-05 (Edge Case): Verify zero or negative reference raises ValueError."""
    with pytest.raises(ValueError):
        normalize(5.0, reference=0.0)

    with pytest.raises(ValueError):
        normalize(5.0, reference=-10.0)


def test_tc_2_1_06_preset_weights_sum_to_one():
    """TC-2.1-06: Verify all 4 business presets sum strictly to 1.0."""
    for name, weights in PRESETS.items():
        total = sum(weights.to_tuple())
        assert math.isclose(total, 1.0, rel_tol=1e-6), (
            f"Preset '{name}' sum is {total} != 1.0"
        )

    # Check named constants directly
    for preset in (MINIMIZE_DISTANCE, MINIMIZE_COST_FUEL, PRIORITIZE_SLA, BALANCED):
        assert math.isclose(sum(preset.to_tuple()), 1.0, rel_tol=1e-6)

    # Check getter
    assert get_preset_weights("minimize_distance") == MINIMIZE_DISTANCE
    assert get_preset_weights("balanced") == BALANCED


def test_tc_2_1_07_fitness_unit_safety():
    """
    TC-2.1-07: Verify normalization ensures unit-safety across disparate scales.
    Raw km (e.g. 500 km) should not dwarf a penalty term (e.g. 2 penalty units)
    when both are properly normalized relative to baselines.
    """
    # Raw route with long distance (500 km) and 2 SLA penalty units
    baseline = {"ref_distance_km": 500.0, "ref_time_min": 600.0, "ref_congestion_ratio": 1.0}

    # Normalized evaluation
    eval_result = evaluate_route_cost(
        distance_km=550.0,          # 10% over distance baseline (norm = 1.1)
        time_min=660.0,              # 10% over time baseline (norm = 1.1)
        congestion_ratio=1.1,        # 10% over congestion baseline (norm = 1.1)
        sla_soft_signal=1.1,         # 1.1 SLA signal
        baseline=baseline,
        preset="balanced",           # equal 0.25 weights
    )

    # All normalized components are 1.1
    assert eval_result["norm_distance"] == pytest.approx(1.1)
    assert eval_result["norm_time"] == pytest.approx(1.1)
    assert eval_result["norm_congestion"] == pytest.approx(1.1)
    assert eval_result["sla_soft_signal"] == pytest.approx(1.1)
    assert eval_result["fitness"] == pytest.approx(1.1)


def test_tc_2_1_08_end_to_end_route_evaluation():
    """TC-2.1-08: Verify end-to-end route fitness calculation with various presets."""
    baseline = compute_route_baseline(
        baseline_distance_km=25.0,
        baseline_time_min=45.0,
    )

    # Test with Balanced preset
    eval_balanced = evaluate_route_cost(
        distance_km=30.0,
        time_min=50.0,
        congestion_ratio=1.2,
        sla_soft_signal=0.1,
        baseline=baseline,
        preset="balanced",
    )
    assert math.isfinite(eval_balanced["fitness"])
    assert eval_balanced["fitness"] > 0.0

    # Test with Prioritize SLA preset
    eval_sla = evaluate_route_cost(
        distance_km=30.0,
        time_min=50.0,
        congestion_ratio=1.2,
        sla_soft_signal=0.1,
        baseline=baseline,
        preset="prioritize_sla",
    )
    assert math.isfinite(eval_sla["fitness"])

    # Test with invalid weights sum raises error in calculate_fitness
    with pytest.raises(ValueError):
        calculate_fitness(1.0, 1.0, 1.0, 1.0, (0.5, 0.5, 0.5, 0.5))  # sum = 2.0 != 1.0
