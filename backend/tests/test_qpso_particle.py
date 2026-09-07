"""
backend/tests/test_qpso_particle.py — Milestone 4.1 Test Suite

Test Cases:
  TC-4.1-01: Arrival time computed correctly on simple 2-stop route
  TC-4.1-02: Monotonicity property holds (later departure -> later arrival)
  TC-4.1-03: Out-of-bounds particle position clamped to valid bounds (negative test)
  TC-4.1-04: Multi-stop cumulative arrival timestamps are exact
  TC-4.1-05: Empty / single-stop routes handled cleanly without error (edge case)
"""

import pytest

from app.qpso.arrival_simulator import simulate_trip_arrivals
from app.qpso.particle import QPSOParticle, compute_mbest


def test_tc_4_1_01_simple_arrival_time_calculation():
    """
    TC-4.1-01: Verify arrival simulation on a simple 2-stop route.
    Departure: 480 min (08:00 AM)
    WH -> P1: 10 min base travel, 1.2x congestion -> 12 min travel. Arrival P1 = 492.
    P1 service: 5 min -> Departure P1 = 497.
    P1 -> P2: 15 min base travel, 1.0x congestion -> 15 min travel. Arrival P2 = 512.
    P2 service: 5 min -> Departure P2 = 517.
    P2 -> WH: 20 min base travel, 1.0x congestion -> 20 min travel. Return WH = 537.
    Total duration: 537 - 480 = 57 min.
    """
    travel_times = {
        ("WH-1", "P1"): 10.0,
        ("P1", "P2"): 15.0,
        ("P2", "WH-1"): 20.0,
    }
    congestion = {
        ("WH-1", "P1"): 1.2,
        ("P1", "P2"): 1.0,
        ("P2", "WH-1"): 1.0,
    }

    result = simulate_trip_arrivals(
        departure_time_min=480.0,
        warehouse_id="WH-1",
        stops=["P1", "P2"],
        travel_time_lookup=travel_times,
        congestion_lookup=congestion,
        service_time_min=5.0,
    )

    assert result.departure_time_min == 480.0
    assert len(result.stop_arrivals) == 2

    # Stop 1
    s1 = result.stop_arrivals[0]
    assert s1.stop_id == "P1"
    assert s1.arrival_time_min == pytest.approx(492.0)
    assert s1.departure_time_min == pytest.approx(497.0)

    # Stop 2
    s2 = result.stop_arrivals[1]
    assert s2.stop_id == "P2"
    assert s2.arrival_time_min == pytest.approx(512.0)
    assert s2.departure_time_min == pytest.approx(517.0)

    # Warehouse Return
    assert result.return_arrival_time_min == pytest.approx(537.0)
    assert result.total_duration_min == pytest.approx(57.0)


def test_tc_4_1_02_monotonicity_holds():
    """TC-4.1-02: Shifting departure by +30 min shifts all stop arrivals by exactly +30 min."""
    travel_times = {("WH-1", "P1"): 10.0, ("P1", "WH-1"): 10.0}

    res_t0 = simulate_trip_arrivals(
        departure_time_min=480.0,
        warehouse_id="WH-1",
        stops=["P1"],
        travel_time_lookup=travel_times,
    )
    res_t30 = simulate_trip_arrivals(
        departure_time_min=510.0,
        warehouse_id="WH-1",
        stops=["P1"],
        travel_time_lookup=travel_times,
    )

    assert res_t30.stop_arrivals[0].arrival_time_min == pytest.approx(
        res_t0.stop_arrivals[0].arrival_time_min + 30.0
    )
    assert res_t30.return_arrival_time_min == pytest.approx(
        res_t0.return_arrival_time_min + 30.0
    )


def test_tc_4_1_03_out_of_bounds_clamped():
    """TC-4.1-03 (Negative): Particle positions outside operating bounds are clamped."""
    # Bounds: [360, 1200]
    p = QPSOParticle(position=[100.0, 1500.0], bounds=(360.0, 1200.0))

    assert p.position[0] == 360.0  # Clamped up to min
    assert p.position[1] == 1200.0  # Clamped down to max

    # Test update with quantum step clamping
    p.update_quantum_position(
        gbest_position=[1200.0, 1200.0],
        mbest_position=[1200.0, 1200.0],
        beta=1.5,
    )
    assert 360.0 <= p.position[0] <= 1200.0
    assert 360.0 <= p.position[1] <= 1200.0


def test_tc_4_1_04_multi_stop_cumulative_arrival():
    """TC-4.1-04: 5-stop route cumulative arrival and departure chain."""
    stops = [f"P{i}" for i in range(1, 6)]
    result = simulate_trip_arrivals(
        departure_time_min=500.0,
        warehouse_id="WH-1",
        stops=stops,
        service_time_min=5.0,
        default_travel_time_min=10.0,
    )

    assert len(result.stop_arrivals) == 5
    prev_dep = 500.0
    for s in result.stop_arrivals:
        assert s.arrival_time_min == pytest.approx(prev_dep + 10.0)
        assert s.departure_time_min == pytest.approx(s.arrival_time_min + 5.0)
        prev_dep = s.departure_time_min

    # Final return
    assert result.return_arrival_time_min == pytest.approx(prev_dep + 10.0)


def test_tc_4_1_05_empty_and_single_stop_route():
    """TC-4.1-05 (Edge Case): Empty and single-stop routes handle cleanly."""
    res_empty = simulate_trip_arrivals(departure_time_min=480.0, warehouse_id="WH-1", stops=[])
    assert res_empty.stop_arrivals == []
    assert res_empty.total_duration_min == 0.0

    res_single = simulate_trip_arrivals(
        departure_time_min=480.0,
        warehouse_id="WH-1",
        stops=["P1"],
        default_travel_time_min=8.0,
        service_time_min=3.0,
    )
    assert len(res_single.stop_arrivals) == 1
    assert res_single.stop_arrivals[0].arrival_time_min == pytest.approx(488.0)
    assert res_single.return_arrival_time_min == pytest.approx(499.0)  # 488 + 3 + 8 = 499


def test_tc_4_1_06_mbest_computation():
    """Verify mean-best calculation across swarm."""
    p1 = QPSOParticle(position=[400.0, 500.0])
    p2 = QPSOParticle(position=[600.0, 700.0])

    mbest = compute_mbest([p1, p2])
    assert mbest[0] == pytest.approx(500.0)
    assert mbest[1] == pytest.approx(600.0)
