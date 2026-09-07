"""
backend/app/traffic/fallback_curve.py — Milestone 5.2

Simulated time-of-day congestion fallback curve per spec §3c point 5:
Provides a deterministic, pure-function time-of-day traffic model for Pune
when TomTom API is offline, unconfigured, or rate-limited.
Zero external dependencies.
"""

from __future__ import annotations

import math
from typing import Any

from app.traffic.tomtom_client import FlowSegmentReading


def get_time_of_day_congestion(time_minutes: float, road_class: str = "primary") -> float:
    """
    Calculate multiplicative congestion ratio based on time of day in Pune.

    Time is canonical minutes since midnight (0.0 to 1440.0).
    Pune traffic profile:
      - Morning rush (09:00 - 11:30 = 540 - 690 min), peak around 10:00 (600 min) -> ratio ~ 1.8 - 2.2
      - Evening rush (17:30 - 20:30 = 1050 - 1230 min), peak around 19:00 (1140 min) -> ratio ~ 2.0 - 2.5
      - Afternoon lull (13:00 - 15:30 = 780 - 930 min) -> ratio ~ 1.2 - 1.4
      - Night / Early morning (22:00 - 06:30) -> ratio ~ 1.0 (free flow)

    Args:
        time_minutes: Minutes since midnight [0, 1440).
        road_class: OSM road type (motorway, trunk, primary, secondary, tertiary, residential).

    Returns:
        Multiplicative congestion ratio (>= 1.0).
    """
    # Wrap to 24h cycle
    t = float(time_minutes) % 1440.0

    # Base baseline congestion
    ratio = 1.0

    # Gaussian helper for peak curve
    def gaussian(x: float, mu: float, sigma: float, amplitude: float) -> float:
        return amplitude * math.exp(-0.5 * ((x - mu) / sigma) ** 2)

    # Morning Peak (mean 10:00 = 600m, width ~ 60m)
    morning = gaussian(t, mu=600.0, sigma=50.0, amplitude=1.05)

    # Evening Peak (mean 19:00 = 1140m, width ~ 70m)
    evening = gaussian(t, mu=1140.0, sigma=65.0, amplitude=1.35)

    # Midday moderate traffic (mean 14:00 = 840m)
    midday = gaussian(t, mu=840.0, sigma=100.0, amplitude=0.25)

    # Road class sensitivity factor
    class_multipliers = {
        "motorway": 0.85,
        "trunk": 0.95,
        "primary": 1.05,
        "secondary": 1.00,
        "tertiary": 0.90,
        "residential": 0.80,
    }
    class_mult = class_multipliers.get(road_class.lower(), 1.0)

    total_peak = (morning + evening + midday) * class_mult
    ratio = 1.0 + max(0.0, total_peak)

    # Upper cap at 3.0 (gridlock threshold)
    return max(1.0, min(3.0, round(ratio, 3)))


def generate_fallback_readings(
    segments: list[dict[str, Any]],
    time_minutes: float = 600.0,
) -> list[FlowSegmentReading]:
    """
    Synthesize FlowSegmentReading objects for a catalog of segments using the fallback curve.

    Args:
        segments: List of representative segment dicts with segment_id, lat, lon, road_class.
        time_minutes: Simulated time in minutes since midnight.

    Returns:
        List of FlowSegmentReading with source='simulated_fallback'.
    """
    readings: list[FlowSegmentReading] = []
    base_free_flow = 40.0  # Typical urban arterial free-flow speed in km/h

    for seg in segments:
        seg_id = seg.get("segment_id", "UNKNOWN")
        lat = float(seg.get("lat", 18.5204))
        lon = float(seg.get("lon", 73.8567))
        road_class = seg.get("road_class", "primary")

        ratio = get_time_of_day_congestion(time_minutes, road_class=road_class)
        current_speed = round(base_free_flow / ratio, 1)

        readings.append(
            FlowSegmentReading(
                segment_id=seg_id,
                lat=lat,
                lon=lon,
                current_speed_kmh=current_speed,
                free_flow_speed_kmh=base_free_flow,
                congestion_ratio=ratio,
                confidence=0.7,
                source="simulated_fallback",
                raw_response={"simulated": True, "time_minutes": time_minutes, "road_class": road_class},
            )
        )

    return readings
