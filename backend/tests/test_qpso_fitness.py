"""
backend/tests/test_qpso_fitness.py — Milestone 4.2 Test Suite

Test Cases:
  TC-4.2-01: Feasible route identified with valid departure times
  TC-4.2-02: Genuinely infeasible route flagged with feasible=False
  TC-4.2-03: Barely feasible route correctly marked feasible (not misflagged)
  TC-4.2-04: Fitness reflects w4 weighting from session preset
  TC-4.2-05: Multiple independent SLA windows on single route evaluated strictly
  TC-4.2-06: Integration pipeline: QGA route output fed into QPSO timing optimization
"""


from app.qga.run_qga import run_qga
from app.qpso.run_qpso import QPSOResult, run_qpso


def test_tc_4_2_01_feasible_route_found():
    """TC-4.2-01: Feasible route with generous SLA window (500-700 min) finds feasible schedule."""
    routes = {
        "VEH-001": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": ["P1", "P2"]}],
    }
    # Generous SLA: 09:00 - 12:00 (540 - 720 min)
    sla_lookup = {
        "P1": (540, 720),
        "P2": (540, 720),
    }
    travel_times = {
        ("WH-1", "P1"): 10.0,
        ("P1", "P2"): 10.0,
        ("P2", "WH-1"): 10.0,
    }

    result = run_qpso(
        decoded_routes=routes,
        sla_lookup=sla_lookup,
        travel_time_lookup=travel_times,
        bounds=(480.0, 600.0),
        seed=42,
    )

    assert isinstance(result, QPSOResult)
    assert result.feasible is True
    assert len(result.infeasible_routes) == 0
    assert "VEH-001" in result.best_departure_times


def test_tc_4_2_02_infeasible_route_flagged():
    """TC-4.2-02: Impossible SLA window (1 min window after 30 min travel) flagged infeasible."""
    routes = {
        "VEH-001": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": ["P1"]}],
    }
    # Earliest warehouse departure is 360 min. Travel takes 60 min -> earliest arrival = 420 min.
    # SLA requires delivery by 380 min (impossible!)
    sla_lookup = {
        "P1": (360, 380),
    }
    travel_times = {
        ("WH-1", "P1"): 60.0,
        ("P1", "WH-1"): 60.0,
    }

    result = run_qpso(
        decoded_routes=routes,
        sla_lookup=sla_lookup,
        travel_time_lookup=travel_times,
        bounds=(360.0, 600.0),
        seed=42,
    )

    assert result.feasible is False
    assert len(result.infeasible_routes) == 1
    assert result.infeasible_routes[0]["vehicle_id"] == "VEH-001"


def test_tc_4_2_03_tight_feasible_not_misflagged():
    """TC-4.2-03 (Negative): Tight but reachable window correctly declared feasible."""
    routes = {
        "VEH-001": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": ["P1"]}],
    }
    # Travel = 15 min. Departure at 485 min -> arrival at 500 min. SLA = [500, 505].
    sla_lookup = {"P1": (500, 505)}
    travel_times = {("WH-1", "P1"): 15.0, ("P1", "WH-1"): 15.0}

    result = run_qpso(
        decoded_routes=routes,
        sla_lookup=sla_lookup,
        travel_time_lookup=travel_times,
        bounds=(480.0, 500.0),
        seed=42,
    )

    assert result.feasible is True
    assert len(result.infeasible_routes) == 0


def test_tc_4_2_04_fitness_reflects_preset_w4():
    """TC-4.2-04: Prioritize SLA preset applies higher w4 weight to SLA lateness."""
    routes = {
        "VEH-001": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": ["P1"]}],
    }
    sla_lookup = {"P1": (400, 410)}  # Will be violated by departure at 480
    travel_times = {("WH-1", "P1"): 10.0, ("P1", "WH-1"): 10.0}

    res_sla_preset = run_qpso(
        decoded_routes=routes,
        sla_lookup=sla_lookup,
        travel_time_lookup=travel_times,
        preset="prioritize_sla",  # w4 = 0.50
        max_iterations=1,
        seed=42,
    )

    res_dist_preset = run_qpso(
        decoded_routes=routes,
        sla_lookup=sla_lookup,
        travel_time_lookup=travel_times,
        preset="minimize_distance",  # w4 = 0.15
        max_iterations=1,
        seed=42,
    )

    assert res_sla_preset.best_fitness > res_dist_preset.best_fitness


def test_tc_4_2_05_multiple_sla_windows_evaluated_independently():
    """TC-4.2-05 (Edge Case): Multi-stop trip with one late stop flags the whole trip."""
    routes = {
        "VEH-001": [{"trip_number": 1, "warehouse_id": "WH-1", "stops": ["P1", "P2"]}],
    }
    # P1 is easy (08:00-12:00), but P2 is set impossibly early (07:00-07:15)
    sla_lookup = {
        "P1": (480, 720),
        "P2": (420, 435),
    }
    travel_times = {
        ("WH-1", "P1"): 10.0,
        ("P1", "P2"): 20.0,
        ("P2", "WH-1"): 20.0,
    }

    result = run_qpso(
        decoded_routes=routes,
        sla_lookup=sla_lookup,
        travel_time_lookup=travel_times,
        bounds=(480.0, 600.0),
        seed=42,
    )

    assert result.feasible is False
    assert len(result.infeasible_routes) == 1


def test_tc_4_2_06_qga_to_qpso_pipeline_integration():
    """TC-4.2-06 (Integration): QGA route output seamlessly feeds into QPSO timing optimizer."""
    stops = [f"PAR-PUNE-{i:04d}" for i in range(1, 11)]
    sla_lookup = {s: (540, 720) for s in stops}  # 09:00 - 12:00 window
    vehicles = ["VEH-001", "VEH-002"]

    # Step 1: Run QGA combinatorial optimization
    qga_res = run_qga(
        stops=stops,
        vehicles=vehicles,
        warehouse_id="WH-PUNE-001",
        pop_size=15,
        max_generations=15,
        seed=42,
    )

    # Step 2: Run QPSO continuous departure timing optimization
    qpso_res = run_qpso(
        decoded_routes=qga_res.decoded_routes,
        sla_lookup=sla_lookup,
        bounds=(480.0, 600.0),
        max_iterations=20,
        seed=42,
    )

    assert isinstance(qpso_res, QPSOResult)
    assert qpso_res.feasible is True
    assert len(qpso_res.best_departure_times) == 2
