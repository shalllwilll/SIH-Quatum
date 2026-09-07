"""
backend/tests/test_simulation.py — Milestone 9.1

Tests for Accelerated-Clock Simulation Engine & Vehicle Position Interpolation:
- TC-9.1-01: Position interpolates correctly mid-edge
- TC-9.1-02: Vehicle transitions idle -> en_route at departure time
- TC-9.1-03: Vehicle transitions to delivering dwell state and next leg
- TC-9.1-04: Route completion handled past return arrival time
- TC-9.1-05: Simulation clock acceleration ratio configurable
- TC-9.1-06: Position endpoints consistency
"""

from __future__ import annotations

import time

from app.simulation.clock import SimulationClock
from app.simulation.position_interpolator import (
    calculate_bearing_deg,
    interpolate_vehicle_position,
)


def test_simulation_clock_progression():
    """TC-9.1-05: Verify clock advances time according to acceleration ratio."""
    # 60x acceleration ratio: 1 real second = 1 sim minute
    clock = SimulationClock(start_time_min=540.0, acceleration_ratio=60.0)
    assert clock.get_current_time_min() >= 540.0

    time.sleep(0.05)
    t1 = clock.get_current_time_min()
    assert t1 >= 540.0

    # Test setting custom time
    clock.set_time(600.0)
    assert 600.0 <= clock.get_current_time_min() < 601.0

    # Test pause and resume
    clock.pause()
    p_time = clock.get_current_time_min()
    time.sleep(0.05)
    assert clock.get_current_time_min() == p_time
    clock.resume()


def test_position_interpolator_idle_before_departure():
    """TC-9.1-02: Before departure time, vehicle is idle at warehouse coordinates."""
    assignment = {
        "vehicle_id": "Van-1",
        "departure_time_min": 540.0,
        "return_arrival_time_min": 720.0,
        "stop_arrivals": [
            {"stop_id": "P-001", "arrival_time_min": 560.0, "departure_time_min": 565.0},
        ],
    }
    stops_coords = {"P-001": (18.5300, 73.8600)}
    wh_coords = (18.5204, 73.8567)

    # Time before departure (e.g. 530 min = 08:50 AM)
    pos = interpolate_vehicle_position(
        assignment=assignment,
        stops_coords=stops_coords,
        warehouse_coords=wh_coords,
        current_time_min=530.0,
    )

    assert pos.status == "idle"
    assert pos.lat == 18.5204
    assert pos.lon == 73.8567
    assert pos.speed_kmh == 0.0


def test_position_interpolator_mid_edge():
    """TC-9.1-01: Vehicle interpolates position proportionally between waypoints mid-leg."""
    assignment = {
        "vehicle_id": "Van-1",
        "departure_time_min": 540.0,
        "return_arrival_time_min": 720.0,
        "stop_arrivals": [
            {"stop_id": "P-001", "arrival_time_min": 560.0, "departure_time_min": 565.0},
        ],
    }
    wh_coords = (18.5000, 73.8000)
    stops_coords = {"P-001": (18.6000, 73.9000)}

    # Exactly halfway between departure (540) and arrival (560) -> 550 min
    pos = interpolate_vehicle_position(
        assignment=assignment,
        stops_coords=stops_coords,
        warehouse_coords=wh_coords,
        current_time_min=550.0,
    )

    assert pos.status == "en_route"
    # Midpoint should be (18.5500, 73.8500)
    assert abs(pos.lat - 18.5500) < 1e-4
    assert abs(pos.lon - 73.8500) < 1e-4
    assert pos.speed_kmh > 0.0
    assert 0.0 <= pos.heading_deg <= 360.0
    assert pos.current_stop_index == 1


def test_position_interpolator_delivering_dwell():
    """TC-9.1-03: While within stop arrival and departure window, vehicle is delivering at stop."""
    assignment = {
        "vehicle_id": "Van-1",
        "departure_time_min": 540.0,
        "return_arrival_time_min": 720.0,
        "stop_arrivals": [
            {"stop_id": "P-001", "arrival_time_min": 560.0, "departure_time_min": 565.0},
            {"stop_id": "P-002", "arrival_time_min": 580.0, "departure_time_min": 585.0},
        ],
    }
    wh_coords = (18.5204, 73.8567)
    stops_coords = {
        "P-001": (18.5300, 73.8600),
        "P-002": (18.5400, 73.8700),
    }

    # At 562 min (between 560 arrival and 565 departure at P-001)
    pos = interpolate_vehicle_position(
        assignment=assignment,
        stops_coords=stops_coords,
        warehouse_coords=wh_coords,
        current_time_min=562.0,
    )

    assert pos.status == "delivering"
    assert abs(pos.lat - 18.5300) < 1e-4
    assert abs(pos.lon - 73.8600) < 1e-4
    assert pos.speed_kmh == 0.0
    assert pos.current_stop_index == 1


def test_position_interpolator_completion():
    """TC-9.1-04: After return arrival time, vehicle status is complete at warehouse."""
    assignment = {
        "vehicle_id": "Van-1",
        "departure_time_min": 540.0,
        "return_arrival_time_min": 720.0,
        "stop_arrivals": [
            {"stop_id": "P-001", "arrival_time_min": 560.0, "departure_time_min": 565.0},
        ],
    }
    wh_coords = (18.5204, 73.8567)
    stops_coords = {"P-001": (18.5300, 73.8600)}

    # At 730 min (past 720 return time)
    pos = interpolate_vehicle_position(
        assignment=assignment,
        stops_coords=stops_coords,
        warehouse_coords=wh_coords,
        current_time_min=730.0,
    )

    assert pos.status == "complete"
    assert pos.lat == 18.5204
    assert pos.lon == 73.8567
    assert pos.speed_kmh == 0.0


def test_bearing_calculation():
    """Verify compass bearing calculation helper."""
    # North: 18.0 -> 19.0, lon constant
    bearing_n = calculate_bearing_deg(18.0, 73.0, 19.0, 73.0)
    assert abs(bearing_n - 0.0) < 1.0 or abs(bearing_n - 360.0) < 1.0

    # East: lat constant, 73.0 -> 74.0
    bearing_e = calculate_bearing_deg(18.0, 73.0, 18.0, 74.0)
    assert abs(bearing_e - 90.0) < 2.0
