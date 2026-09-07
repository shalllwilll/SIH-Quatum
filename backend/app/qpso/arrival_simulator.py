"""
backend/app/qpso/arrival_simulator.py — Milestone 4.1

Simulates vehicle departure, travel, delivery dwell time, and cumulative arrival
times across all stops in a scheduled route under graph congestion per spec §3d.
Reuses Milestone 2.1's physics module (edge_travel_time) as the single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.costing.physics import CongestionMode, edge_travel_time


@dataclass
class StopArrival:
    stop_id: str
    arrival_time_min: float
    departure_time_min: float
    travel_time_min: float
    service_time_min: float


@dataclass
class TripArrivalResult:
    stop_arrivals: list[StopArrival]
    departure_time_min: float
    return_arrival_time_min: float
    total_duration_min: float

    def get_arrival(self, stop_id: str) -> float | None:
        """Lookup arrival time for a specific stop."""
        for s in self.stop_arrivals:
            if s.stop_id == stop_id:
                return s.arrival_time_min
        return None


def simulate_trip_arrivals(
    departure_time_min: float,
    warehouse_id: str,
    stops: list[str],
    travel_time_lookup: dict[tuple[str, str], float] | None = None,
    congestion_lookup: dict[tuple[str, str], float] | None = None,
    service_time_min: float = 5.0,
    congestion_mode: str | CongestionMode = CongestionMode.MULTIPLICATIVE,
    default_travel_time_min: float = 10.0,
) -> TripArrivalResult:
    """
    Simulate arrival and departure timestamps along a vehicle trip.

    Args:
        departure_time_min: Vehicle dispatch time in minutes since midnight.
        warehouse_id: Origin and return warehouse ID.
        stops: Ordered sequence of delivery stop IDs.
        travel_time_lookup: Precomputed baseline travel time between locations.
        congestion_lookup: Multiplicative congestion ratio or additive delay between locations.
        service_time_min: Delivery service/dwell time at each stop (default 5.0 min).
        congestion_mode: Congestion mode ("multiplicative" or "additive").
        default_travel_time_min: Fallback travel time between stops when lookup is missing.

    Returns:
        TripArrivalResult containing per-stop arrival records and return time.
    """
    if not stops:
        return TripArrivalResult(
            stop_arrivals=[],
            departure_time_min=departure_time_min,
            return_arrival_time_min=departure_time_min,
            total_duration_min=0.0,
        )

    current_time = float(departure_time_min)
    prev_loc = warehouse_id
    stop_arrivals: list[StopArrival] = []

    for stop_id in stops:
        base_time = default_travel_time_min
        if travel_time_lookup is not None:
            base_time = travel_time_lookup.get((prev_loc, stop_id), default_travel_time_min)

        cong_val = 1.0 if str(congestion_mode).lower() == "multiplicative" else 0.0
        if congestion_lookup is not None:
            cong_val = congestion_lookup.get((prev_loc, stop_id), cong_val)

        # Physics calculation (Milestone 2.1)
        t_travel = edge_travel_time(base_time, cong_val, mode=congestion_mode)

        arrival_time = current_time + t_travel
        departure_from_stop = arrival_time + service_time_min

        stop_arrivals.append(
            StopArrival(
                stop_id=stop_id,
                arrival_time_min=arrival_time,
                departure_time_min=departure_from_stop,
                travel_time_min=t_travel,
                service_time_min=service_time_min,
            )
        )

        current_time = departure_from_stop
        prev_loc = stop_id

    # Return leg to warehouse
    return_base_time = default_travel_time_min
    if travel_time_lookup is not None:
        return_base_time = travel_time_lookup.get((prev_loc, warehouse_id), default_travel_time_min)

    return_cong_val = 1.0 if str(congestion_mode).lower() == "multiplicative" else 0.0
    if congestion_lookup is not None:
        return_cong_val = congestion_lookup.get((prev_loc, warehouse_id), return_cong_val)

    t_return = edge_travel_time(return_base_time, return_cong_val, mode=congestion_mode)
    return_arrival_time = current_time + t_return
    total_duration = return_arrival_time - departure_time_min

    return TripArrivalResult(
        stop_arrivals=stop_arrivals,
        departure_time_min=departure_time_min,
        return_arrival_time_min=return_arrival_time,
        total_duration_min=total_duration,
    )


def simulate_fleet_arrivals(
    decoded_routes: dict[str, list[dict[str, Any]]],
    departure_times_min: dict[str, float] | list[float],
    travel_time_lookup: dict[tuple[str, str], float] | None = None,
    congestion_lookup: dict[tuple[str, str], float] | None = None,
    service_time_min: float = 5.0,
    congestion_mode: str | CongestionMode = CongestionMode.MULTIPLICATIVE,
) -> dict[str, list[TripArrivalResult]]:
    """
    Simulate arrival times across an entire fleet of decoded vehicle routes.

    Args:
        decoded_routes: Output of decode_chromosome(): {vehicle_id: [trip_dict, ...]}.
        departure_times_min: Dict {vehicle_id: dep_time} or vector of departure times.

    Returns:
        Dict mapping vehicle_id -> list of TripArrivalResult objects.
    """
    results: dict[str, list[TripArrivalResult]] = {}
    dep_idx = 0

    for vehicle_id, trips in decoded_routes.items():
        results[vehicle_id] = []
        for trip in trips:
            if isinstance(departure_times_min, dict):
                dep_time = departure_times_min.get(vehicle_id, 480.0)
            elif isinstance(departure_times_min, list) and dep_idx < len(departure_times_min):
                dep_time = departure_times_min[dep_idx]
                dep_idx += 1
            else:
                dep_time = 480.0  # Default 08:00 AM

            wh_id = trip.get("warehouse_id", "WH-PUNE-001")
            stops = trip.get("stops", [])

            sim_result = simulate_trip_arrivals(
                departure_time_min=dep_time,
                warehouse_id=wh_id,
                stops=stops,
                travel_time_lookup=travel_time_lookup,
                congestion_lookup=congestion_lookup,
                service_time_min=service_time_min,
                congestion_mode=congestion_mode,
            )
            results[vehicle_id].append(sim_result)

    return results
