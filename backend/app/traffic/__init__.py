"""
Traffic package — Milestone 5.1 & 5.2.
Live traffic integration, TomTom API proxy, segment sampling, and congestion propagation.
"""

from app.traffic.propagate import (
    find_nearest_representative_segment,
    propagate_congestion_to_graph,
)
from app.traffic.tomtom_client import FlowSegmentReading, TomTomClient

__all__ = [
    "FlowSegmentReading",
    "TomTomClient",
    "find_nearest_representative_segment",
    "propagate_congestion_to_graph",
]
