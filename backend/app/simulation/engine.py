"""
backend/app/simulation/engine.py — Live Fleet Simulation Engine

Background asyncio task that:
  1. Watches for a currently-assigned routing session.
  2. On each tick (every 1 real second = 1 simulated minute at 60x speed),
     interpolates every vehicle's position along its assigned route geometry.
  3. Broadcasts telemetry to all connected fleet WebSocket clients.
  4. Can be re-started whenever a new assignment is committed via the /assign endpoint.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

log = logging.getLogger(__name__)

# Singleton reference to the currently running simulation loop task
_sim_task: asyncio.Task | None = None
# The session document currently being simulated
_active_session: dict[str, Any] | None = None


def get_active_session() -> dict[str, Any] | None:
    return _active_session


async def _simulation_loop(session: dict[str, Any], ws_manager: Any, clock: Any) -> None:
    """
    Core simulation loop.
    Runs every 1 real second. Broadcasts interpolated vehicle positions to all WS clients.
    Stops when the simulation clock has passed all vehicles' return times.
    """
    from app.simulation.position_interpolator import interpolate_vehicle_position

    assignments: list[dict] = session.get("vehicle_assignments", [])
    if not assignments:
        log.warning("Simulation started but no vehicle_assignments found in session.")
        return

    # Build warehouse lookup: vehicle_id → (lat, lon) of its assigned warehouse
    warehouse_map: dict[str, tuple[float, float]] = {}
    STRATEGIC_WAREHOUSES = [
        ("WH-PUNE-001", 18.5308, 73.8475),
        ("WH-PUNE-002", 18.5529, 73.9242),
        ("WH-PUNE-003", 18.5074, 73.8077),
    ]
    # Default central warehouse
    default_wh = (18.5308, 73.8475)
    for a in assignments:
        wh_id = a.get("warehouse_id", "WH-PUNE-001")
        matched = next((w for w in STRATEGIC_WAREHOUSES if w[0] == wh_id), None)
        warehouse_map[a.get("vehicle_id", "")] = (matched[1], matched[2]) if matched else default_wh

    # Build stop_coords from stop_arrivals which contain lat/lon baked in
    def build_stop_coords(assignment: dict) -> dict[str, tuple[float, float]]:
        coords: dict[str, tuple[float, float]] = {}
        for stop in assignment.get("stop_arrivals", []):
            sid = stop.get("stop_id")
            lat = stop.get("lat") or stop.get("latitude")
            lon = stop.get("lon") or stop.get("longitude")
            if sid and lat and lon:
                coords[sid] = (float(lat), float(lon))
        return coords

    # Find the maximum return time among all vehicles — simulation ends then
    max_ret_time = max(
        (float(a.get("return_arrival_time_min", 1020.0)) for a in assignments),
        default=1020.0,
    )

    log.info(
        "Simulation loop started — %d vehicles, max return %.1f min",
        len(assignments),
        max_ret_time,
    )

    ROUTE_COLORS = [
        "#6366f1", "#10b981", "#f59e0b", "#ef4444",
        "#8b5cf6", "#06b6d4", "#ec4899", "#14b8a6", "#f97316", "#3b82f6",
    ]

    try:
        while True:
            current_time = clock.get_current_time_min()

            # Build vehicle telemetry payload
            vehicle_states: list[dict] = []
            all_complete = True

            for idx, assignment in enumerate(assignments):
                vid = assignment.get("vehicle_id", f"V{idx}")
                wh_coords = warehouse_map.get(vid, default_wh)
                stop_coords = build_stop_coords(assignment)
                color = ROUTE_COLORS[idx % len(ROUTE_COLORS)]

                try:
                    pos = interpolate_vehicle_position(
                        assignment=assignment,
                        stops_coords=stop_coords,
                        warehouse_coords=wh_coords,
                        current_time_min=current_time,
                    )
                    if pos.status not in ("complete", "idle"):
                        all_complete = False

                    vehicle_states.append({
                        "vehicle_id": vid,
                        "location": {"lat": pos.lat, "lon": pos.lon},
                        "heading_deg": pos.heading_deg,
                        "speed_kmh": pos.speed_kmh,
                        "status": pos.status,
                        "current_stop_index": pos.current_stop_index,
                        "total_stops": pos.total_stops,
                        "color": color,
                        "route_geometry": assignment.get("route_geometry", []),
                        "stop_arrivals": assignment.get("stop_arrivals", []),
                    })
                except Exception as e:
                    log.debug("Error interpolating vehicle %s: %s", vid, e)
                    vehicle_states.append({
                        "vehicle_id": vid,
                        "location": {"lat": wh_coords[0], "lon": wh_coords[1]},
                        "status": "idle",
                        "color": color,
                        "route_geometry": assignment.get("route_geometry", []),
                        "stop_arrivals": assignment.get("stop_arrivals", []),
                    })

            payload = {
                "type": "telemetry_update",
                "vehicles": vehicle_states,
                "clock": {
                    "time_min": round(current_time, 2),
                    "multiplier": clock.acceleration_ratio,
                    "paused": clock._paused,
                    "time_formatted": _format_time(current_time),
                },
                "session_id": session.get("id", session.get("_id", "")),
            }

            await ws_manager.broadcast_fleet(payload)

            # Check if all vehicles have completed their routes
            if all_complete and current_time > max_ret_time:
                log.info("All vehicles completed routes — simulation loop ending.")
                # Send a final 'simulation_complete' event
                await ws_manager.broadcast_fleet({
                    "type": "simulation_complete",
                    "session_id": session.get("id", ""),
                    "vehicles": vehicle_states,
                })
                break

            await asyncio.sleep(1.0)  # 1 real second = 1 simulated minute (at 60x speed)

    except asyncio.CancelledError:
        log.info("Simulation loop cancelled.")
    except Exception as e:
        log.error("Simulation loop error: %s", e, exc_info=True)


def _format_time(minutes_since_midnight: float) -> str:
    """Format minutes since midnight as HH:MM."""
    total = int(minutes_since_midnight) % 1440
    hh = total // 60
    mm = total % 60
    return f"{hh:02d}:{mm:02d}"


async def start_simulation(session: dict[str, Any]) -> None:
    """
    Start or restart the simulation for the given assigned session.
    Cancels any previously running simulation first.
    Resets the simulation clock to 09:00 AM.
    """
    global _sim_task, _active_session

    from app.simulation.clock import sim_clock
    from app.routers.websocket import manager as ws_manager

    # Cancel any running simulation
    if _sim_task and not _sim_task.done():
        _sim_task.cancel()
        try:
            await _sim_task
        except asyncio.CancelledError:
            pass
        log.info("Previous simulation cancelled.")

    # Reset clock to 09:00 AM
    sim_clock.reset(start_time_min=540.0)

    _active_session = session

    # Start new background loop
    _sim_task = asyncio.create_task(
        _simulation_loop(session, ws_manager, sim_clock),
        name="fleet_sim_loop",
    )
    log.info("Fleet simulation started for session %s", session.get("id", ""))


def stop_simulation() -> None:
    """Stop the currently running simulation."""
    global _sim_task
    if _sim_task and not _sim_task.done():
        _sim_task.cancel()
        log.info("Simulation stopped.")
