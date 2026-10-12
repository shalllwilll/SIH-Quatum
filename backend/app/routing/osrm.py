"""
backend/app/routing/osrm.py — Open Source Routing Machine (OSRM) Road Geometry Service

Provides high-resolution street-snapped road geometry, turning paths, and turn-by-turn
route polylines for last-mile delivery routes across Pune.
Includes in-memory caching and graceful fallback to direct waypoints.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"

# In-memory LRU cache for route geometries to prevent redundant queries
_GEOMETRY_CACHE: dict[str, dict[str, Any]] = {}
_MAX_CACHE_SIZE = 500


def _compute_cache_key(waypoints: list[dict[str, float]]) -> str:
    """Hash waypoints to 5 decimal places for robust cache hits."""
    norm = [(round(wp["lat"], 5), round(wp["lon"], 5)) for wp in waypoints]
    raw = json.dumps(norm, sort_keys=True)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


async def fetch_osrm_route_geometry(
    waypoints: list[dict[str, float]],
    timeout_sec: float = 4.0,
) -> dict[str, Any]:
    """
    Query OSRM public API to fetch street-snapped road geometry for a sequence of waypoints.

    Args:
        waypoints: Ordered list of dicts with 'lat' and 'lon'.
        timeout_sec: Network timeout limit.

    Returns:
        Dict with 'coordinates' (list of [lat, lon]), 'distance_km', 'duration_min', and 'source'.
    """
    if len(waypoints) < 2:
        direct = [[wp["lat"], wp["lon"]] for wp in waypoints]
        return {
            "coordinates": direct,
            "distance_km": 0.0,
            "duration_min": 0.0,
            "source": "direct_fallback",
            "points_count": len(direct),
        }

    cache_key = _compute_cache_key(waypoints)
    if cache_key in _GEOMETRY_CACHE:
        return _GEOMETRY_CACHE[cache_key]

    # OSRM expects: {lon},{lat};{lon},{lat};...
    # Chunk long sequences if > 25 waypoints to avoid URL length limits
    chunk_size = 25
    all_coords: list[list[float]] = []
    total_dist_meters = 0.0
    total_dur_seconds = 0.0
    any_osrm_success = False

    try:
        async with httpx.AsyncClient(
            timeout=timeout_sec,
            headers={"User-Agent": "AbraxasRouting/1.0"},
        ) as client:
            i = 0
            while i < len(waypoints) - 1:
                sub_waypoints = waypoints[i : i + chunk_size]
                if len(sub_waypoints) < 2:
                    break

                coords_str = ";".join(f"{wp['lon']:.6f},{wp['lat']:.6f}" for wp in sub_waypoints)
                url = f"{OSRM_BASE_URL}/{coords_str}?overview=full&geometries=geojson"

                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        route = data["routes"][0]
                        geom_coords = route.get("geometry", {}).get("coordinates", [])
                        # OSRM returns [lon, lat]; convert to Leaflet [lat, lon]
                        converted = [[pt[1], pt[0]] for pt in geom_coords]

                        # Avoid duplicating junction point between chunks
                        if all_coords and converted:
                            all_coords.extend(converted[1:])
                        else:
                            all_coords.extend(converted)

                        total_dist_meters += route.get("distance", 0.0)
                        total_dur_seconds += route.get("duration", 0.0)
                        any_osrm_success = True
                    else:
                        # Fallback for this chunk
                        for wp in sub_waypoints:
                            all_coords.append([wp["lat"], wp["lon"]])
                else:
                    log.warning("OSRM returned status %d for chunk, using direct lines", res.status_code)
                    for wp in sub_waypoints:
                        all_coords.append([wp["lat"], wp["lon"]])

                # Advance with 1-stop overlap for smooth continuity
                i += chunk_size - 1

    except Exception as exc:
        log.debug("OSRM route geometry fetch failed or timed out: %s. Using direct waypoints.", exc)
        all_coords = [[wp["lat"], wp["lon"]] for wp in waypoints]
        any_osrm_success = False

    if not all_coords:
        all_coords = [[wp["lat"], wp["lon"]] for wp in waypoints]

    result = {
        "coordinates": all_coords,
        "distance_km": round(total_dist_meters / 1000.0, 2),
        "duration_min": round(total_dur_seconds / 60.0, 1),
        "source": "osrm" if any_osrm_success else "direct_fallback",
        "points_count": len(all_coords),
    }

    # Store in memory cache
    if len(_GEOMETRY_CACHE) >= _MAX_CACHE_SIZE:
        _GEOMETRY_CACHE.pop(next(iter(_GEOMETRY_CACHE)))
    _GEOMETRY_CACHE[cache_key] = result

    return result
