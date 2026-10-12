"""
backend/app/simulation/position_interpolator.py — Milestone 9.1

Vehicle Position Interpolator:
Interpolates vehicle GPS coordinates (lat, lon, heading, speed, status) along assigned
route stops at any given simulated time. Handles idle -> en_route -> delivering -> complete transitions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class InterpolatedPosition:
    """State of an interpolated vehicle at a specific point in time."""

    lat: float
    lon: float
    heading_deg: float
    speed_kmh: float
    status: str
    current_stop_index: int
    total_stops: int


def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate compass heading angle in degrees (0-360) between two coordinates."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing_rad = math.atan2(y, x)
    bearing_deg = (math.degrees(bearing_rad) + 360.0) % 360.0
    return round(bearing_deg, 1)


def interpolate_vehicle_position(
    assignment: dict[str, Any],
    stops_coords: dict[str, tuple[float, float]],
    warehouse_coords: tuple[float, float] = (18.5204, 73.8567),
    current_time_min: float = 540.0,
) -> InterpolatedPosition:
    """
    Compute real-time interpolated position for an assigned vehicle.

    Args:
        assignment: Vehicle assignment dictionary containing stop_arrivals and departure times.
        stops_coords: Dict mapping stop/parcel IDs to (lat, lon).
        warehouse_coords: Warehouse starting/ending coordinates.
        current_time_min: Current simulation clock time in minutes since midnight.

    Returns:
        InterpolatedPosition containing precise lat, lon, heading, speed, and status.
    """
    dep_time = float(assignment.get("departure_time_min", 540.0))
    ret_time = float(assignment.get("return_arrival_time_min", dep_time + 120.0))
    stop_arrivals = assignment.get("stop_arrivals", [])

    total_stops = len(stop_arrivals)
    wh_lat, wh_lon = warehouse_coords

    # Case 1: Before shift departure (Vehicle is Idle at Warehouse)
    if current_time_min < dep_time:
        return InterpolatedPosition(
            lat=wh_lat,
            lon=wh_lon,
            heading_deg=0.0,
            speed_kmh=0.0,
            status="idle",
            current_stop_index=0,
            total_stops=total_stops,
        )

    # Case 2: After final return to Warehouse (Shift Complete)
    if current_time_min >= ret_time:
        return InterpolatedPosition(
            lat=wh_lat,
            lon=wh_lon,
            heading_deg=0.0,
            speed_kmh=0.0,
            status="complete",
            current_stop_index=total_stops,
            total_stops=total_stops,
        )

    geom = assignment.get("route_geometry", [])
    
    # Pre-calculate active driving times for polyline interpolation
    total_active_time = 0.0
    if geom and len(geom) > 1:
        prev_d = dep_time
        for stop in stop_arrivals:
            arr = float(stop.get("arrival_time_min", prev_d))
            total_active_time += max(0.0, arr - prev_d)
            prev_d = float(stop.get("departure_time_min", arr + 5.0))
        total_active_time += max(0.0, ret_time - prev_d)

    def get_snapped_coords(curr_time: float) -> tuple[float, float, float] | None:
        """Return (lat, lon, heading) based on polyline progress, or None if fallback."""
        if not geom or len(geom) < 2 or total_active_time <= 0:
            return None
        active_time_so_far = 0.0
        prev_d_inner = dep_time
        for s in stop_arrivals:
            arr_inner = float(s.get("arrival_time_min", prev_d_inner))
            dep_inner = float(s.get("departure_time_min", arr_inner + 5.0))
            if curr_time < arr_inner:
                active_time_so_far += max(0.0, curr_time - prev_d_inner)
                break
            else:
                active_time_so_far += max(0.0, arr_inner - prev_d_inner)
                if curr_time <= dep_inner:
                    break
            prev_d_inner = dep_inner
        else:
            active_time_so_far += max(0.0, curr_time - prev_d_inner)
            
        P = min(1.0, max(0.0, active_time_so_far / total_active_time))
        idx_f = P * (len(geom) - 1)
        idx = int(idx_f)
        idx_next = min(idx + 1, len(geom) - 1)
        progress_segment = idx_f - idx
        
        c_lat = geom[idx][0] + progress_segment * (geom[idx_next][0] - geom[idx][0])
        c_lon = geom[idx][1] + progress_segment * (geom[idx_next][1] - geom[idx][1])
        if idx == idx_next:
            h = 0.0
        else:
            h = calculate_bearing_deg(geom[idx][0], geom[idx][1], geom[idx_next][0], geom[idx_next][1])
        return (c_lat, c_lon, h)

    # Case 3: Vehicle is actively executing route legs
    prev_coords = (wh_lat, wh_lon)
    prev_dep_time = dep_time

    for idx, stop in enumerate(stop_arrivals):
        stop_id = stop.get("stop_id", f"STOP-{idx}")
        arr_time = float(stop.get("arrival_time_min", prev_dep_time + 10.0))
        # Dwell time for delivery (5 mins if not specified)
        stop_dep_time = float(stop.get("departure_time_min", arr_time + 5.0))

        stop_lat_lon = stops_coords.get(stop_id)
        if not stop_lat_lon:
            hash_val = sum(ord(c) for c in stop_id)
            stop_lat_lon = (
                wh_lat + (((hash_val * 7) % 30) - 15) * 0.003,
                wh_lon + (((hash_val * 11) % 30) - 15) * 0.003,
            )

        target_lat, target_lon = stop_lat_lon

        # Leg 3A: En-route between previous location and this stop
        if current_time_min < arr_time:
            snapped = get_snapped_coords(current_time_min)
            if snapped:
                curr_lat, curr_lon, heading = snapped
            else:
                time_delta = max(0.001, arr_time - prev_dep_time)
                progress = max(0.0, min(1.0, (current_time_min - prev_dep_time) / time_delta))
                curr_lat = prev_coords[0] + progress * (target_lat - prev_coords[0])
                curr_lon = prev_coords[1] + progress * (target_lon - prev_coords[1])
                heading = calculate_bearing_deg(prev_coords[0], prev_coords[1], target_lat, target_lon)

            return InterpolatedPosition(
                lat=round(curr_lat, 6),
                lon=round(curr_lon, 6),
                heading_deg=heading,
                speed_kmh=32.0,
                status="en_route",
                current_stop_index=idx + 1,
                total_stops=total_stops,
            )

        # Leg 3B: Stationary at Stop (Delivering / Dwell Window)
        if current_time_min <= stop_dep_time:
            return InterpolatedPosition(
                lat=round(target_lat, 6),
                lon=round(target_lon, 6),
                heading_deg=0.0,
                speed_kmh=0.0,
                status="delivering",
                current_stop_index=idx + 1,
                total_stops=total_stops,
            )

        prev_coords = (target_lat, target_lon)
        prev_dep_time = stop_dep_time

    # Leg 3C: Return leg from last stop back to warehouse
    snapped = get_snapped_coords(current_time_min)
    if snapped:
        curr_lat, curr_lon, heading = snapped
    else:
        time_delta = max(0.001, ret_time - prev_dep_time)
        progress = max(0.0, min(1.0, (current_time_min - prev_dep_time) / time_delta))
        curr_lat = prev_coords[0] + progress * (wh_lat - prev_coords[0])
        curr_lon = prev_coords[1] + progress * (wh_lon - prev_coords[1])
        heading = calculate_bearing_deg(prev_coords[0], prev_coords[1], wh_lat, wh_lon)

    return InterpolatedPosition(
        lat=round(curr_lat, 6),
        lon=round(curr_lon, 6),
        heading_deg=heading,
        speed_kmh=35.0,
        status="en_route",
        current_stop_index=total_stops,
        total_stops=total_stops,
    )
