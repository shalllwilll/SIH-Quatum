"""
backend/app/traffic/tomtom_client.py — Milestone 5.1

TomTom Flow Segment Data API client:
Fetches real-time traffic speeds for representative arterial road segments in Pune.
All requests are proxied strictly through the backend (API key is never exposed to frontends).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)

TOMTOM_FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"


@dataclass
class FlowSegmentReading:
    """Parsed real-time traffic reading for a road segment."""
    segment_id: str
    lat: float
    lon: float
    current_speed_kmh: float
    free_flow_speed_kmh: float
    congestion_ratio: float
    confidence: float
    source: str = "live"
    raw_response: dict[str, Any] | None = None


class TomTomClient:
    """Async client for querying TomTom Traffic Flow APIs."""

    def __init__(self, api_key: str | None = None, timeout_sec: float = 5.0):
        self.api_key = api_key if api_key is not None else os.environ.get("TOMTOM_API_KEY", "")
        self.timeout_sec = timeout_sec

    def is_configured(self) -> bool:
        """Check if a non-placeholder API key is set."""
        return bool(self.api_key and "your_tomtom_api_key" not in self.api_key.lower())

    async def fetch_flow_segment(
        self,
        lat: float,
        lon: float,
        segment_id: str = "UNKNOWN",
    ) -> FlowSegmentReading:
        """
        Query TomTom Flow Segment Data API for a single lat/lon coordinate.

        Args:
            lat: Latitude of point on road.
            lon: Longitude of point on road.
            segment_id: Identifier for the representative road segment.

        Returns:
            FlowSegmentReading dataclass.

        Raises:
            ValueError: If API key is missing.
            RuntimeError: If TomTom API returns non-200 or connection fails.
        """
        if not self.is_configured():
            raise ValueError(
                "TOMTOM_API_KEY is not configured in backend/.env. "
                "Please set a valid TomTom API key."
            )

        import httpx

        params = {
            "point": f"{lat},{lon}",
            "key": self.api_key,
            "unit": "KMPH",
        }

        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            response = await client.get(TOMTOM_FLOW_URL, params=params)

            if response.status_code == 429:
                raise RuntimeError("TomTom API rate limit exceeded (HTTP 429).")
            if response.status_code == 403:
                raise RuntimeError("Invalid TomTom API key or unauthorized (HTTP 403).")
            if response.status_code != 200:
                raise RuntimeError(
                    f"TomTom API request failed with status {response.status_code}: {response.text[:200]}"
                )

            data = response.json()
            flow_data = data.get("flowSegmentData", {})

            current_speed = float(flow_data.get("currentSpeed", 30.0))
            free_flow_speed = float(flow_data.get("freeFlowSpeed", 30.0))
            confidence = float(flow_data.get("confidence", 1.0))

            # Multiplicative congestion ratio = freeFlowSpeed / currentSpeed (>= 1.0)
            if current_speed > 0:
                ratio = max(1.0, round(free_flow_speed / current_speed, 3))
            else:
                ratio = 3.0  # Gridlock upper cap

            return FlowSegmentReading(
                segment_id=segment_id,
                lat=lat,
                lon=lon,
                current_speed_kmh=current_speed,
                free_flow_speed_kmh=free_flow_speed,
                congestion_ratio=ratio,
                confidence=confidence,
                source="live",
                raw_response=flow_data,
            )
