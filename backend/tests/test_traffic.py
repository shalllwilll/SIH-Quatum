"""
backend/tests/test_traffic.py — Milestone 5.1

Test cases:
- TC-5.1-01: TomTom client fetches and parses flow segment data correctly
- TC-5.1-02: Invalid/missing API key error handling (ValueError / RuntimeError)
- TC-5.1-03: Spatial propagation assigns congestion_ratio to 100% of graph edges
- TC-5.1-04: Equidistant segment tie-breaking is deterministic (lexicographical)
- TC-5.1-05: Request budget & QPS stay within TomTom free-tier limits
- TC-5.1-06: Security check: API key never exposed in frontend source files
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import networkx as nx
import pytest

from app.traffic.propagate import (
    _haversine_distance_km,
    find_nearest_representative_segment,
    propagate_congestion_to_graph,
)
from app.traffic.tomtom_client import FlowSegmentReading, TomTomClient


@pytest.mark.asyncio
async def test_tomtom_client_fetch_mocked():
    """TC-5.1-01: Verify TomTom client queries and computes multiplicative congestion_ratio."""
    mock_payload = {
        "flowSegmentData": {
            "frc": "FRC1",
            "currentSpeed": 20.0,
            "freeFlowSpeed": 40.0,
            "currentTravelTime": 120,
            "freeFlowTravelTime": 60,
            "confidence": 0.95,
        }
    }

    client = TomTomClient(api_key="mock_valid_key_12345")

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: mock_payload
        mock_get.return_value = mock_response

        reading = await client.fetch_flow_segment(18.5314, 73.8446, segment_id="SEG-001")

        assert isinstance(reading, FlowSegmentReading)
        assert reading.segment_id == "SEG-001"
        assert reading.lat == 18.5314
        assert reading.lon == 73.8446
        assert reading.current_speed_kmh == 20.0
        assert reading.free_flow_speed_kmh == 40.0
        # Multiplicative congestion ratio = 40 / 20 = 2.0
        assert reading.congestion_ratio == 2.0
        assert reading.confidence == 0.95
        assert reading.source == "live"


@pytest.mark.asyncio
async def test_tomtom_client_zero_speed_cap():
    """TC-5.1-01 (subcase): Verify zero current speed caps congestion ratio at gridlock limit (3.0)."""
    mock_payload = {
        "flowSegmentData": {
            "currentSpeed": 0.0,
            "freeFlowSpeed": 35.0,
            "confidence": 0.8,
        }
    }

    client = TomTomClient(api_key="mock_valid_key_12345")

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: mock_payload
        mock_get.return_value = mock_response

        reading = await client.fetch_flow_segment(18.52, 73.85, segment_id="SEG-GRIDLOCK")
        assert reading.congestion_ratio == 3.0


@pytest.mark.asyncio
async def test_tomtom_client_missing_or_placeholder_key():
    """TC-5.1-02: Missing or placeholder API key raises clear ValueError."""
    client_empty = TomTomClient(api_key="")
    assert not client_empty.is_configured()

    with pytest.raises(ValueError, match="TOMTOM_API_KEY is not configured"):
        await client_empty.fetch_flow_segment(18.5, 73.8)

    client_placeholder = TomTomClient(api_key="your_tomtom_api_key_here")
    assert not client_placeholder.is_configured()

    with pytest.raises(ValueError, match="TOMTOM_API_KEY is not configured"):
        await client_placeholder.fetch_flow_segment(18.5, 73.8)


@pytest.mark.asyncio
async def test_tomtom_client_http_errors():
    """TC-5.1-02: HTTP 403 and 429 raise explicit RuntimeError."""
    client = TomTomClient(api_key="mock_key")

    with patch("httpx.AsyncClient.get") as mock_get:
        # Rate limit (429)
        mock_resp_429 = AsyncMock()
        mock_resp_429.status_code = 429
        mock_get.return_value = mock_resp_429
        with pytest.raises(RuntimeError, match="rate limit exceeded"):
            await client.fetch_flow_segment(18.5, 73.8)

        # Unauthorized (403)
        mock_resp_403 = AsyncMock()
        mock_resp_403.status_code = 403
        mock_get.return_value = mock_resp_403
        with pytest.raises(RuntimeError, match="Invalid TomTom API key"):
            await client.fetch_flow_segment(18.5, 73.8)


def test_propagation_assigns_all_edges():
    """TC-5.1-03: Congestion propagation updates 100% of graph edges with valid fields."""
    # Create synthetic test graph
    g = nx.MultiDiGraph()
    g.add_node(1, x=73.8446, y=18.5314)
    g.add_node(2, x=73.8415, y=18.5236)
    g.add_node(3, x=73.8567, y=18.5204)
    g.add_edge(1, 2, key=0, length=1200.0)
    g.add_edge(2, 3, key=0, length=1800.0)
    g.add_edge(3, 1, key=0, length=2400.0)

    readings = [
        FlowSegmentReading(
            segment_id="SEG-001",
            lat=18.5314,
            lon=73.8446,
            current_speed_kmh=20.0,
            free_flow_speed_kmh=40.0,
            congestion_ratio=2.0,
            confidence=1.0,
            source="live",
        ),
        FlowSegmentReading(
            segment_id="SEG-002",
            lat=18.5236,
            lon=73.8415,
            current_speed_kmh=30.0,
            free_flow_speed_kmh=30.0,
            congestion_ratio=1.0,
            confidence=1.0,
            source="live",
        ),
    ]

    updated_count = propagate_congestion_to_graph(g, readings)
    assert updated_count == 3

    for _u, _v, _k, data in g.edges(keys=True, data=True):
        assert "congestion_ratio" in data
        assert data["congestion_ratio"] >= 1.0
        assert data["congestion_type"] == "multiplicative"
        assert data["traffic_source"] == "live"
        assert data["associated_segment_id"] in ("SEG-001", "SEG-002")


def test_propagation_equidistant_tie_breaking():
    """TC-5.1-04: Deterministic tie-breaking on equidistant segments uses lexicographical order."""
    # Target at (lon=73.8000, lat=18.5000)
    target_lon, target_lat = 73.8000, 18.5000

    # Two segments exactly equidistant north and south (delta lat = 0.01)
    reading_a = FlowSegmentReading(
        segment_id="SEG-002",
        lat=18.5100,
        lon=73.8000,
        current_speed_kmh=15.0,
        free_flow_speed_kmh=30.0,
        congestion_ratio=2.0,
        confidence=1.0,
    )
    reading_b = FlowSegmentReading(
        segment_id="SEG-001",
        lat=18.4900,
        lon=73.8000,
        current_speed_kmh=25.0,
        free_flow_speed_kmh=30.0,
        congestion_ratio=1.2,
        confidence=1.0,
    )

    # Distances are identical
    dist_a = _haversine_distance_km(target_lon, target_lat, reading_a.lon, reading_a.lat)
    dist_b = _haversine_distance_km(target_lon, target_lat, reading_b.lon, reading_b.lat)
    assert abs(dist_a - dist_b) < 1e-6

    # Regardless of list ordering, SEG-001 must win because 'SEG-001' < 'SEG-002'
    winner_1 = find_nearest_representative_segment(target_lon, target_lat, [reading_a, reading_b])
    winner_2 = find_nearest_representative_segment(target_lon, target_lat, [reading_b, reading_a])

    assert winner_1.segment_id == "SEG-001"
    assert winner_2.segment_id == "SEG-001"


def test_budget_calculation_and_qps():
    """TC-5.1-05: Verify 70-80 segments over 30 min refresh cycle stay well within free tier."""
    representative_path = Path(__file__).resolve().parent.parent / "data" / "representative_segments.json"
    with open(representative_path, encoding="utf-8") as f:
        segments = json.load(f)

    num_segments = len(segments)
    assert 60 <= num_segments <= 80, f"Representative segment count {num_segments} outside 60-80 target."

    # Spec §3c: 120s refresh cycle over a 30-min demo = 15 refresh cycles
    demo_duration_minutes = 30
    refresh_interval_seconds = 120
    cycles = (demo_duration_minutes * 60) // refresh_interval_seconds  # 15 cycles

    total_requests_demo = num_segments * cycles
    # Free tier limit: 2500 calls/day
    free_tier_daily_limit = 2500
    assert total_requests_demo <= free_tier_daily_limit
    assert total_requests_demo <= 1200

    # Instantaneous QPS staggering (spec specifies staggering at ~8 req/sec <= 10 QPS cap)
    stagger_qps = 8.0
    time_to_query_all_sec = num_segments / stagger_qps
    assert time_to_query_all_sec < refresh_interval_seconds  # Querying 70 takes ~8.75s, well within 120s


def test_security_api_key_not_in_frontend():
    """TC-5.1-06: Ensure no TomTom API key string or secret token exists in frontend codebase."""
    workspace_root = Path(__file__).resolve().parent.parent.parent
    frontend_dirs = [workspace_root / "frontend-admin", workspace_root / "frontend-driver"]

    sensitive_patterns = ["TOMTOM_API_KEY", "tomtom.com/traffic", "flowSegmentData"]

    for frontend_dir in frontend_dirs:
        if not frontend_dir.exists():
            continue
        for root, _dirs, files in os.walk(frontend_dir):
            if "node_modules" in root or ".git" in root or "dist" in root:
                continue
            for file in files:
                if file.endswith((".js", ".jsx", ".ts", ".tsx", ".html", ".env")):
                    file_path = Path(root) / file
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for pattern in sensitive_patterns:
                        assert pattern not in content, (
                            f"Security violation: Found sensitive pattern '{pattern}' in frontend file {file_path}"
                        )
