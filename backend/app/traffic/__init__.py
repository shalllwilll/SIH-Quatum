"""
Traffic package — Milestone 5.1 & 5.2.
Live traffic integration, TomTom API proxy, segment sampling, caching,
staggered refresh cycle, and graceful degradation fallback.
"""

from app.traffic.cache import TrafficCache
from app.traffic.fallback_curve import (
    generate_fallback_readings,
    get_time_of_day_congestion,
)
from app.traffic.propagate import (
    find_nearest_representative_segment,
    propagate_congestion_to_graph,
)
from app.traffic.refresh_loop import TrafficRefreshManager
from app.traffic.tomtom_client import FlowSegmentReading, TomTomClient

__all__ = [
    "FlowSegmentReading",
    "TomTomClient",
    "TrafficCache",
    "TrafficRefreshManager",
    "find_nearest_representative_segment",
    "generate_fallback_readings",
    "get_time_of_day_congestion",
    "propagate_congestion_to_graph",
]
