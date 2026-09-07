"""
backend/app/traffic/refresh_loop.py — Milestone 5.2

Traffic refresh loop and lifecycle manager per spec §3c points 4 & 5:
- 120-second scheduled refresh cycle.
- Staggered requests at ~8 req/sec (125ms delay) to never exceed 10 QPS cap.
- Graceful error handling with per-segment caching and fallback curve triggering.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from app.traffic.cache import TrafficCache
from app.traffic.fallback_curve import generate_fallback_readings
from app.traffic.tomtom_client import FlowSegmentReading, TomTomClient

log = logging.getLogger(__name__)

DEFAULT_SEGMENTS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "representative_segments.json"


class TrafficRefreshManager:
    """Manages the periodic polling, staggering, caching, and fallback of TomTom traffic data."""

    def __init__(
        self,
        client: TomTomClient | None = None,
        cache: TrafficCache | None = None,
        segments_catalog: list[dict[str, Any]] | None = None,
        refresh_interval_sec: float = 120.0,
        stagger_delay_sec: float = 0.125,
        fallback_threshold: int = 3,
    ):
        self.client = client or TomTomClient()
        self.cache = cache or TrafficCache(fallback_threshold=fallback_threshold)
        self.refresh_interval_sec = refresh_interval_sec
        self.stagger_delay_sec = stagger_delay_sec
        self.fallback_threshold = fallback_threshold
        self._is_running = False
        self._loop_task: asyncio.Task | None = None

        # Load representative segments
        if segments_catalog is not None:
            self.segments = segments_catalog
        else:
            if DEFAULT_SEGMENTS_PATH.exists():
                with open(DEFAULT_SEGMENTS_PATH, encoding="utf-8") as f:
                    self.segments = json.load(f)
            else:
                self.segments = []

        # Handle cold start initialization
        if self.cache.is_cold_start() and self.segments:
            initial_readings = generate_fallback_readings(self.segments, time_minutes=600.0)
            for r in initial_readings:
                self.cache.update_reading(r)

    def get_current_readings(self) -> list[FlowSegmentReading]:
        """Return current readings from cache."""
        return self.cache.get_all_readings()

    async def refresh_cycle(self, time_minutes: float = 600.0) -> dict[str, Any]:
        """
        Execute one complete staggered polling cycle across all representative segments.

        Args:
            time_minutes: Current simulated time in minutes since midnight (used for fallback if needed).

        Returns:
            Dictionary with cycle results summary.
        """
        if not self.segments:
            return {"status": "no_segments", "success_count": 0, "failure_count": 0}

        # If TomTom client is unconfigured, record failure and trigger fallback immediately
        if not self.client.is_configured():
            log.warning("TomTom client is not configured with a valid key. Running fallback curve.")
            self.cache.record_cycle_failure(time_minutes=time_minutes, catalog=self.segments)
            return {
                "status": "fallback_unconfigured",
                "traffic_source": self.cache.traffic_source,
                "success_count": 0,
                "failure_count": len(self.segments),
            }

        success_count = 0
        failure_count = 0

        for seg in self.segments:
            seg_id = seg["segment_id"]
            lat = float(seg["lat"])
            lon = float(seg["lon"])

            try:
                reading = await self.client.fetch_flow_segment(lat, lon, segment_id=seg_id)
                self.cache.update_reading(reading)
                success_count += 1
            except Exception as exc:
                failure_count += 1
                log.debug("Segment %s fetch failed (%s); retaining cached value.", seg_id, exc)

            # Stagger requests to avoid bursting QPS
            if self.stagger_delay_sec > 0:
                await asyncio.sleep(self.stagger_delay_sec)

        # Evaluate whole-cycle health
        if success_count > 0:
            self.cache.record_cycle_success()
        else:
            self.cache.record_cycle_failure(time_minutes=time_minutes, catalog=self.segments)

        return {
            "status": "completed",
            "traffic_source": self.cache.traffic_source,
            "success_count": success_count,
            "failure_count": failure_count,
            "total_segments": len(self.segments),
        }

    async def start_loop(self, stop_event: asyncio.Event | None = None) -> None:
        """Run the background refresh loop at the configured interval."""
        self._is_running = True
        log.info("Started traffic refresh loop (interval=%ds, stagger=%0.3fs).", self.refresh_interval_sec, self.stagger_delay_sec)

        try:
            while self._is_running and (stop_event is None or not stop_event.is_set()):
                await self.refresh_cycle()
                # Wait for next cycle or cancellation
                try:
                    await asyncio.wait_for(
                        asyncio.shield(stop_event.wait()) if stop_event else asyncio.sleep(self.refresh_interval_sec),
                        timeout=self.refresh_interval_sec if stop_event else None,
                    )
                except TimeoutError:
                    pass
        except asyncio.CancelledError:
            log.info("Traffic refresh loop cancelled.")
        finally:
            self._is_running = False

    def stop_loop(self) -> None:
        """Signal the background loop to stop."""
        self._is_running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
