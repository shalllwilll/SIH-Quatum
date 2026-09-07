"""
backend/tests/test_traffic_fallback.py — Milestone 5.2

Test cases:
- TC-5.2-01: Cache serves last good value on temporary API failure
- TC-5.2-02: Refresh cycle runs on schedule and updates segment readings
- TC-5.2-03: Staggering respects QPS limit (125ms delay = 8 req/sec <= 10 QPS)
- TC-5.2-04: Persistent failures (>=3 cycles) switch source to simulated_fallback
- TC-5.2-05: Recovery from fallback when live API succeeds
- TC-5.2-06: Cold start serves non-null simulated default without crashing
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from app.traffic.cache import TrafficCache
from app.traffic.fallback_curve import (
    get_time_of_day_congestion,
)
from app.traffic.refresh_loop import TrafficRefreshManager
from app.traffic.tomtom_client import FlowSegmentReading, TomTomClient

SAMPLE_SEGMENTS = [
    {"segment_id": "SEG-001", "name": "Shivajinagar", "lat": 18.5314, "lon": 73.8446, "road_class": "primary"},
    {"segment_id": "SEG-002", "name": "FC Road", "lat": 18.5236, "lon": 73.8415, "road_class": "secondary"},
]


def test_tc_5_2_06_cold_start():
    """TC-5.2-06: Cold start provides valid non-null fallback readings immediately."""
    cache = TrafficCache()
    assert cache.is_cold_start()
    assert cache.traffic_source == "simulated_fallback"

    manager = TrafficRefreshManager(
        client=TomTomClient(api_key="mock_key"),
        cache=cache,
        segments_catalog=SAMPLE_SEGMENTS,
    )

    # Before any refresh has run, readings must exist and be valid
    readings = manager.get_current_readings()
    assert len(readings) == 2
    for r in readings:
        assert isinstance(r, FlowSegmentReading)
        assert r.source == "simulated_fallback"
        assert r.congestion_ratio >= 1.0
        assert r.current_speed_kmh > 0


@pytest.mark.asyncio
async def test_tc_5_2_01_cache_serves_last_good_on_failure():
    """TC-5.2-01: Cache serves last good values with 'cached' source on temporary failure."""
    cache = TrafficCache(fallback_threshold=3)
    client = TomTomClient(api_key="mock_key")

    manager = TrafficRefreshManager(
        client=client,
        cache=cache,
        segments_catalog=SAMPLE_SEGMENTS,
        stagger_delay_sec=0.0,  # Speed up tests
    )

    # 1. First cycle succeeds (Live)
    mock_live_reading = FlowSegmentReading(
        segment_id="SEG-001",
        lat=18.5314,
        lon=73.8446,
        current_speed_kmh=20.0,
        free_flow_speed_kmh=40.0,
        congestion_ratio=2.0,
        confidence=1.0,
        source="live",
    )
    with patch.object(client, "fetch_flow_segment", new=AsyncMock(return_value=mock_live_reading)):
        res = await manager.refresh_cycle()
        assert res["status"] == "completed"
        assert cache.traffic_source == "live"
        assert cache.get_reading("SEG-001").congestion_ratio == 2.0
        assert cache.get_reading("SEG-001").source == "live"

    # 2. Second cycle fails (API outage / network drop)
    with patch.object(client, "fetch_flow_segment", new=AsyncMock(side_effect=RuntimeError("TomTom timeout"))):
        res = await manager.refresh_cycle()
        assert res["status"] == "completed"
        # 1 failure < 3 threshold -> traffic_source becomes 'cached'
        assert cache.traffic_source == "cached"
        # Cached congestion_ratio is preserved
        cached_reading = cache.get_reading("SEG-001")
        assert cached_reading.congestion_ratio == 2.0
        assert cached_reading.source == "cached"


@pytest.mark.asyncio
async def test_tc_5_2_04_persistent_failure_triggers_fallback():
    """TC-5.2-04: 3 consecutive cycle failures switch traffic_source to 'simulated_fallback'."""
    cache = TrafficCache(fallback_threshold=3)
    client = TomTomClient(api_key="mock_key")

    manager = TrafficRefreshManager(
        client=client,
        cache=cache,
        segments_catalog=SAMPLE_SEGMENTS,
        stagger_delay_sec=0.0,
    )

    # Initial success to establish live state
    mock_live_reading = FlowSegmentReading(
        segment_id="SEG-001",
        lat=18.5314,
        lon=73.8446,
        current_speed_kmh=35.0,
        free_flow_speed_kmh=40.0,
        congestion_ratio=1.14,
        confidence=1.0,
        source="live",
    )
    with patch.object(client, "fetch_flow_segment", new=AsyncMock(return_value=mock_live_reading)):
        await manager.refresh_cycle()
        assert cache.traffic_source == "live"

    # Now simulate 3 consecutive failures
    with patch.object(client, "fetch_flow_segment", new=AsyncMock(side_effect=RuntimeError("HTTP 503"))):
        # Failure 1
        await manager.refresh_cycle(time_minutes=600.0)
        assert cache.traffic_source == "cached"
        assert cache.get_stats()["consecutive_cycle_failures"] == 1

        # Failure 2
        await manager.refresh_cycle(time_minutes=600.0)
        assert cache.traffic_source == "cached"
        assert cache.get_stats()["consecutive_cycle_failures"] == 2

        # Failure 3 -> triggers fallback curve
        await manager.refresh_cycle(time_minutes=600.0)
        assert cache.traffic_source == "simulated_fallback"
        assert cache.get_stats()["consecutive_cycle_failures"] == 3

        readings = manager.get_current_readings()
        for r in readings:
            assert r.source == "simulated_fallback"


@pytest.mark.asyncio
async def test_tc_5_2_05_recovery_from_fallback():
    """TC-5.2-05: Successful live cycle restores traffic_source to 'live' from fallback."""
    cache = TrafficCache(fallback_threshold=2)
    client = TomTomClient(api_key="mock_key")

    manager = TrafficRefreshManager(
        client=client,
        cache=cache,
        segments_catalog=SAMPLE_SEGMENTS,
        stagger_delay_sec=0.0,
    )

    # Cause persistent failure to enter simulated_fallback
    with patch.object(client, "fetch_flow_segment", new=AsyncMock(side_effect=RuntimeError("Outage"))):
        await manager.refresh_cycle()
        await manager.refresh_cycle()
        assert cache.traffic_source == "simulated_fallback"

    # Recover with successful live fetch
    mock_live = FlowSegmentReading(
        segment_id="SEG-001",
        lat=18.5314,
        lon=73.8446,
        current_speed_kmh=25.0,
        free_flow_speed_kmh=40.0,
        congestion_ratio=1.6,
        confidence=1.0,
        source="live",
    )
    with patch.object(client, "fetch_flow_segment", new=AsyncMock(return_value=mock_live)):
        res = await manager.refresh_cycle()
        assert res["status"] == "completed"
        assert cache.traffic_source == "live"
        assert cache.get_stats()["consecutive_cycle_failures"] == 0
        assert cache.get_reading("SEG-001").source == "live"


@pytest.mark.asyncio
async def test_tc_5_2_03_staggering_qps():
    """TC-5.2-03: Stagger delay ensures request rate remains under 10 QPS."""
    client = TomTomClient(api_key="mock_key")
    stagger_sec = 0.05  # 20 req/sec limit test with small list
    segments = [
        {"segment_id": f"SEG-{i:03d}", "lat": 18.5 + i * 0.001, "lon": 73.8, "road_class": "primary"}
        for i in range(5)
    ]

    manager = TrafficRefreshManager(
        client=client,
        segments_catalog=segments,
        stagger_delay_sec=stagger_sec,
    )

    mock_resp = FlowSegmentReading(
        segment_id="SEG-X",
        lat=18.5,
        lon=73.8,
        current_speed_kmh=30.0,
        free_flow_speed_kmh=30.0,
        congestion_ratio=1.0,
        confidence=1.0,
    )

    t0 = time.perf_counter()
    with patch.object(client, "fetch_flow_segment", new=AsyncMock(return_value=mock_resp)):
        await manager.refresh_cycle()
    elapsed = time.perf_counter() - t0

    # 5 segments with 0.05s stagger should take at least 5 * 0.05 = 0.25s
    assert elapsed >= 0.20


@pytest.mark.asyncio
async def test_tc_5_2_02_scheduled_loop():
    """TC-5.2-02: Background loop triggers cycles periodically."""
    stop_event = asyncio.Event()
    client = TomTomClient(api_key="mock_key")

    manager = TrafficRefreshManager(
        client=client,
        segments_catalog=SAMPLE_SEGMENTS,
        refresh_interval_sec=0.05,  # 50ms fast loop for testing
        stagger_delay_sec=0.0,
    )

    cycle_count = 0
    original_refresh = manager.refresh_cycle

    async def counted_refresh(*args, **kwargs):
        nonlocal cycle_count
        cycle_count += 1
        if cycle_count >= 2:
            stop_event.set()
        return await original_refresh(*args, **kwargs)

    manager.refresh_cycle = counted_refresh

    mock_reading = FlowSegmentReading(
        segment_id="SEG-001",
        lat=18.5,
        lon=73.8,
        current_speed_kmh=30.0,
        free_flow_speed_kmh=30.0,
        congestion_ratio=1.0,
        confidence=1.0,
    )

    with patch.object(client, "fetch_flow_segment", new=AsyncMock(return_value=mock_reading)):
        await manager.start_loop(stop_event=stop_event)

    assert cycle_count >= 2


def test_fallback_curve_rush_hours():
    """Verify fallback curve correctly peaks during Pune morning & evening rush hours."""
    # Midnight (00:00 = 0m) -> Free flow (~1.0)
    midnight_ratio = get_time_of_day_congestion(0.0)
    assert midnight_ratio == 1.0

    # Morning rush peak (10:00 = 600m) -> High congestion (>= 1.8)
    morning_peak = get_time_of_day_congestion(600.0)
    assert 1.8 <= morning_peak <= 2.3

    # Afternoon lull (14:30 = 870m) -> Lower than peak
    afternoon_lull = get_time_of_day_congestion(870.0)
    assert 1.1 <= afternoon_lull < morning_peak

    # Evening rush peak (19:00 = 1140m) -> Highest congestion (>= 2.0)
    evening_peak = get_time_of_day_congestion(1140.0)
    assert 2.0 <= evening_peak <= 2.6
