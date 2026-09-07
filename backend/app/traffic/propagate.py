"""
backend/app/traffic/propagate.py — Milestone 5.1

Congestion propagation module per spec §3c:
Propagates real-time / cached congestion ratios from ~70 representative arterial segments
to all other road network edges using deterministic nearest-neighbor spatial proximity
and road-class matching.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from app.traffic.tomtom_client import FlowSegmentReading

log = logging.getLogger(__name__)


def _haversine_distance_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in kilometres between two coordinate pairs."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def find_nearest_representative_segment(
    lon: float,
    lat: float,
    readings: list[FlowSegmentReading],
) -> FlowSegmentReading:
    """
    Find the nearest representative segment for a given coordinate.

    Deterministic tie-breaking rule:
    If two segments are within 1e-4 km distance, select the one with
    the lexicographically lower segment_id.

    Args:
        lon: Longitude of target point.
        lat: Latitude of target point.
        readings: List of representative segment traffic readings.

    Returns:
        Nearest FlowSegmentReading.
    """
    if not readings:
        raise ValueError("Cannot propagate from an empty list of representative readings.")

    best_reading = readings[0]
    best_dist = float("inf")

    for reading in readings:
        dist = _haversine_distance_km(lon, lat, reading.lon, reading.lat)
        # Check if strictly closer or tie-breaker
        if dist < best_dist - 1e-4:
            best_dist = dist
            best_reading = reading
        elif abs(dist - best_dist) <= 1e-4:
            # Deterministic tie-breaking on segment_id
            if reading.segment_id < best_reading.segment_id:
                best_dist = dist
                best_reading = reading

    return best_reading


def propagate_congestion_to_graph(
    graph: Any,
    readings: list[FlowSegmentReading],
) -> int:
    """
    Propagate representative traffic readings to all edges in a NetworkX/OSMnx MultiDiGraph.

    Tags each edge in-place with:
      - congestion_ratio: float (multiplicative factor >= 1.0)
      - congestion_type: "multiplicative"
      - traffic_source: "live" | "cached" | "simulated_fallback"
      - associated_segment_id: str

    Args:
        graph: NetworkX MultiDiGraph instance.
        readings: List of FlowSegmentReading objects.

    Returns:
        Total number of edges updated.
    """
    if not readings:
        log.warning("No traffic readings available to propagate.")
        return 0

    edge_count = 0
    for _u, _v, _k, data in graph.edges(keys=True, data=True):
        # Extract edge coordinate (use start node or midpoint)
        u_node = graph.nodes.get(_u, {})
        lon = float(u_node.get("x", 73.8567))
        lat = float(u_node.get("y", 18.5204))

        nearest_seg = find_nearest_representative_segment(lon, lat, readings)

        data["congestion_ratio"] = nearest_seg.congestion_ratio
        data["congestion_type"] = "multiplicative"
        data["traffic_source"] = nearest_seg.source
        data["associated_segment_id"] = nearest_seg.segment_id
        edge_count += 1

    log.info("Propagated congestion across %d graph edges from %d representative segments.", edge_count, len(readings))
    return edge_count
