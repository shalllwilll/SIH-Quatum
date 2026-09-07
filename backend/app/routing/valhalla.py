"""
backend/app/routing/valhalla.py — Enterprise Valhalla C++ Routing Engine Integration

Provides a high-performance HTTP client for the Valhalla Open Source Routing Engine:
- Multi-point Distance & Travel Time Matrix API (/sources_to_targets)
- Turn-by-Turn Route Polyline API (/route)
- Unified Matrix Generator with automatic graceful fallback to in-memory spatial graph
"""

from __future__ import annotations

import logging
import math
import os
from typing import Any

import httpx

log = logging.getLogger(__name__)

VALHALLA_DEFAULT_URL = os.getenv("VALHALLA_URL", "http://localhost:8002")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two coordinates."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return float(r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))


class ValhallaClient:
    """
    HTTP Client for local or containerized Valhalla C++ routing engine.
    """

    def __init__(self, base_url: str | None = None, timeout: float = 3.0):
        self.base_url = (base_url or os.getenv("VALHALLA_URL", VALHALLA_DEFAULT_URL)).rstrip("/")
        self.timeout = timeout

    async def is_available(self) -> bool:
        """Check if the Valhalla C++ daemon is reachable and responding."""
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{self.base_url}/status")
                return res.status_code == 200
        except Exception:
            return False

    async def sources_to_targets(
        self,
        sources: list[dict[str, float]],
        targets: list[dict[str, float]],
        costing: str = "auto",
    ) -> dict[str, Any] | None:
        """
        Execute matrix distance and duration computation between sources and targets.

        Args:
            sources: List of dicts with 'lat' and 'lon'.
            targets: List of dicts with 'lat' and 'lon'.
            costing: Routing profile ('auto', 'bicycle', 'pedestrian').

        Returns:
            Parsed Valhalla response dict or None on failure.
        """
        payload = {
            "sources": [{"lat": s["lat"], "lon": s["lon"]} for s in sources],
            "targets": [{"lat": t["lat"], "lon": t["lon"]} for t in targets],
            "costing": costing,
            "costing_options": {
                "auto": {
                    "top_speed": 80.0,
                }
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/sources_to_targets", json=payload)
                if res.status_code == 200:
                    return res.json()
                log.warning("Valhalla matrix returned status %d: %s", res.status_code, res.text)
                return None
        except Exception as exc:
            log.debug("Valhalla connection attempt failed (%s). Using fallback engine.", exc)
            return None

    async def route(
        self,
        locations: list[dict[str, float]],
        costing: str = "auto",
    ) -> dict[str, Any] | None:
        """
        Calculate turn-by-turn route path and polyline shape.

        Args:
            locations: Ordered list of waypoints with 'lat' and 'lon'.
            costing: Routing profile.

        Returns:
            Parsed Valhalla trip document or None on failure.
        """
        if len(locations) < 2:
            return None

        payload = {
            "locations": [{"lat": loc["lat"], "lon": loc["lon"]} for loc in locations],
            "costing": costing,
            "directions_options": {"units": "kilometers"},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/route", json=payload)
                if res.status_code == 200:
                    return res.json()
                return None
        except Exception as exc:
            log.debug("Valhalla route query failed: %s", exc)
            return None


async def get_routing_matrix(
    locations: list[dict[str, Any]],
    valhalla_client: ValhallaClient | None = None,
    default_speed_kmh: float = 30.0,
) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], float]]:
    """
    High-level matrix builder:
    Computes pairwise distance_km and travel_time_min matrices.
    Queries Valhalla C++ matrix when available; gracefully falls back to spatial geometry.

    Args:
        locations: List of location dicts containing 'id', 'lat', 'lon'.
        valhalla_client: Optional ValhallaClient instance.
        default_speed_kmh: Fallback average travel speed.

    Returns:
        Tuple of (distance_matrix, travel_time_matrix).
    """
    client = valhalla_client or ValhallaClient()
    n = len(locations)
    dist_matrix: dict[tuple[str, str], float] = {}
    time_matrix: dict[tuple[str, str], float] = {}

    if n == 0:
        return dist_matrix, time_matrix

    # Check if Valhalla can fulfill this matrix
    coords = [{"lat": float(loc["lat"]), "lon": float(loc["lon"])} for loc in locations]
    valhalla_data = await client.sources_to_targets(sources=coords, targets=coords)

    if valhalla_data and "sources_to_targets" in valhalla_data:
        log.info("Populated distance matrix for %d stops using Valhalla C++ Engine.", n)
        rows = valhalla_data["sources_to_targets"]
        for i, row in enumerate(rows):
            src_id = str(locations[i].get("id", locations[i].get("parcel_id", f"LOC-{i}")))
            for j, cell in enumerate(row):
                tgt_id = str(locations[j].get("id", locations[j].get("parcel_id", f"LOC-{j}")))
                dist_km = float(cell.get("distance", 0.0))
                time_min = float(cell.get("time", 0.0)) / 60.0
                dist_matrix[(src_id, tgt_id)] = dist_km
                time_matrix[(src_id, tgt_id)] = time_min
        return dist_matrix, time_matrix

    # Fallback to high-speed spatial calculation
    for i in range(n):
        src = locations[i]
        src_id = str(src.get("id", src.get("parcel_id", src.get("warehouse_id", f"LOC-{i}"))))
        for j in range(n):
            tgt = locations[j]
            tgt_id = str(tgt.get("id", tgt.get("parcel_id", tgt.get("warehouse_id", f"LOC-{j}"))))
            if i == j:
                dist_matrix[(src_id, tgt_id)] = 0.0
                time_matrix[(src_id, tgt_id)] = 0.0
            else:
                dist = _haversine_km(src["lat"], src["lon"], tgt["lat"], tgt["lon"])
                # Apply 1.25 road winding factor over straight-line haversine
                road_dist = dist * 1.25
                dist_matrix[(src_id, tgt_id)] = road_dist
                time_matrix[(src_id, tgt_id)] = (road_dist / max(default_speed_kmh, 1.0)) * 60.0

    return dist_matrix, time_matrix
