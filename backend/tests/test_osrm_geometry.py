"""
backend/tests/test_osrm_geometry.py — Tests for OSRM Road Geometry and Snapping
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.routing.osrm import _compute_cache_key, fetch_osrm_route_geometry


@pytest.mark.asyncio
async def test_compute_cache_key_deterministic():
    wp1 = [{"lat": 18.52043, "lon": 73.85674}, {"lat": 18.53621, "lon": 73.87442}]
    wp2 = [{"lat": 18.52043, "lon": 73.85674}, {"lat": 18.53621, "lon": 73.87442}]
    assert _compute_cache_key(wp1) == _compute_cache_key(wp2)


@pytest.mark.asyncio
async def test_fetch_osrm_fallback_for_single_point():
    single = [{"lat": 18.5204, "lon": 73.8567}]
    res = await fetch_osrm_route_geometry(single)
    assert res["source"] == "direct_fallback"
    assert res["points_count"] == 1
    assert res["coordinates"] == [[18.5204, 73.8567]]


@pytest.mark.asyncio
async def test_fetch_osrm_route_geometry_or_fallback():
    waypoints = [
        {"lat": 18.5204, "lon": 73.8567},
        {"lat": 18.5362, "lon": 73.8744},
        {"lat": 18.5410, "lon": 73.8820},
    ]
    res = await fetch_osrm_route_geometry(waypoints, timeout_sec=3.0)
    assert "coordinates" in res
    assert len(res["coordinates"]) >= 3
    # Check that each point is [lat, lon] within Pune latitude/longitude range
    for pt in res["coordinates"]:
        assert len(pt) == 2
        assert 18.0 <= pt[0] <= 19.5
        assert 73.0 <= pt[1] <= 74.5


@pytest.mark.asyncio
async def test_api_road_geometry_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "waypoints": [
                {"lat": 18.5204, "lon": 73.8567},
                {"lat": 18.5362, "lon": 73.8744},
                {"lat": 18.5204, "lon": 73.8567},
            ]
        }
        res = await client.post("/routing/road-geometry", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "coordinates" in data
        assert "points_count" in data
        assert data["points_count"] >= 3
        assert data["source"] in ("osrm", "direct_fallback")
