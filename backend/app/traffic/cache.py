"""
backend/app/traffic/cache.py — Milestone 5.2

In-memory traffic cache for representative segment readings.
Maintains segment freshness, failure counts, and determines traffic source
state: "live" | "cached" | "simulated_fallback".
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.traffic.fallback_curve import generate_fallback_readings
from app.traffic.tomtom_client import FlowSegmentReading

log = logging.getLogger(__name__)


class TrafficCache:
    """Thread-safe / async-friendly cache for representative road segment traffic data."""

    def __init__(self, fallback_threshold: int = 3):
        self.fallback_threshold = fallback_threshold
        self._readings: dict[str, FlowSegmentReading] = {}
        self._timestamps: dict[str, float] = {}
        self._consecutive_cycle_failures: int = 0
        self._last_cycle_timestamp: float | None = None
        self._traffic_source: str = "simulated_fallback"

    @property
    def traffic_source(self) -> str:
        """Current operational traffic source: 'live' | 'cached' | 'simulated_fallback'."""
        return self._traffic_source

    def is_cold_start(self) -> bool:
        """Check if cache has never received any live readings."""
        return len(self._readings) == 0

    def update_reading(self, reading: FlowSegmentReading, timestamp: float | None = None) -> None:
        """
        Store or update a segment reading with current timestamp.

        Args:
            reading: FlowSegmentReading to cache.
            timestamp: Epoch timestamp (defaults to time.time()).
        """
        ts = timestamp if timestamp is not None else time.time()
        self._readings[reading.segment_id] = reading
        self._timestamps[reading.segment_id] = ts

    def get_reading(self, segment_id: str) -> FlowSegmentReading | None:
        """Retrieve cached reading for a segment ID."""
        return self._readings.get(segment_id)

    def get_all_readings(self) -> list[FlowSegmentReading]:
        """Return all currently stored segment readings."""
        return list(self._readings.values())

    def get_age_seconds(self, segment_id: str, current_time: float | None = None) -> float | None:
        """Return age of cached reading in seconds, or None if not present."""
        ts = self._timestamps.get(segment_id)
        if ts is None:
            return None
        now = current_time if current_time is not None else time.time()
        return max(0.0, round(now - ts, 2))

    def record_cycle_success(self, timestamp: float | None = None) -> None:
        """
        Record a successful refresh cycle.
        Resets failure count and transitions status to 'live'.
        """
        self._consecutive_cycle_failures = 0
        self._last_cycle_timestamp = timestamp if timestamp is not None else time.time()
        self._traffic_source = "live"

    def record_cycle_failure(
        self,
        time_minutes: float = 600.0,
        catalog: list[dict[str, Any]] | None = None,
        timestamp: float | None = None,
    ) -> None:
        """
        Record a failed refresh cycle.
        Increments failure count and toggles between 'cached' and 'simulated_fallback'.

        Args:
            time_minutes: Minutes since midnight for fallback curve generation.
            catalog: Representative segments catalog for fallback synthesis.
            timestamp: Optional epoch timestamp.
        """
        self._consecutive_cycle_failures += 1
        self._last_cycle_timestamp = timestamp if timestamp is not None else time.time()

        if self._consecutive_cycle_failures >= self.fallback_threshold or self.is_cold_start():
            self._traffic_source = "simulated_fallback"
            log.warning(
                "Persistent TomTom failures (%d >= %d). Switched traffic source to simulated_fallback.",
                self._consecutive_cycle_failures,
                self.fallback_threshold,
            )
            # If fallback active or cold start, synthesize readings from fallback curve
            if catalog:
                fallback_readings = generate_fallback_readings(catalog, time_minutes=time_minutes)
                for r in fallback_readings:
                    self.update_reading(r, timestamp=self._last_cycle_timestamp)
        else:
            self._traffic_source = "cached"
            # Update reading source field to reflect cached status
            for seg_id, reading in self._readings.items():
                if reading.source == "live":
                    self._readings[seg_id] = FlowSegmentReading(
                        segment_id=reading.segment_id,
                        lat=reading.lat,
                        lon=reading.lon,
                        current_speed_kmh=reading.current_speed_kmh,
                        free_flow_speed_kmh=reading.free_flow_speed_kmh,
                        congestion_ratio=reading.congestion_ratio,
                        confidence=reading.confidence * 0.9,  # Decay confidence
                        source="cached",
                        raw_response=reading.raw_response,
                    )
            log.info(
                "TomTom cycle failed (%d consecutive). Serving cached data.",
                self._consecutive_cycle_failures,
            )

    def get_stats(self) -> dict[str, Any]:
        """Return diagnostic metrics on cache state."""
        return {
            "traffic_source": self._traffic_source,
            "cached_segment_count": len(self._readings),
            "consecutive_cycle_failures": self._consecutive_cycle_failures,
            "fallback_threshold": self.fallback_threshold,
            "last_cycle_timestamp": self._last_cycle_timestamp,
        }
