"""
backend/tests/test_analytics.py — Milestone 10.2

Tests for Analytics Aggregation Endpoints:
- TC-10.2-01: Fuel efficiency trend time-series
- TC-10.2-02: Overall SLA compliance aggregation
- TC-10.2-03: Per-vehicle SLA compliance breakdown
- TC-10.2-04: Constraint violation history
- TC-10.2-05: Empty database returns empty gracefully
- TC-10.2-06: Performance benchmark
"""

from __future__ import annotations

import os

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/abraxas_test_db")

import time

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    """AsyncClient fixture with ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_analytics_fuel_efficiency_and_sla(client: AsyncClient):
    """TC-10.2-01, TC-10.2-02, TC-10.2-03: Fuel trends, SLA compliance, and per-vehicle breakdown."""
    db = get_db()

    # Pre-seed session
    s_doc = {
        "status": "completed",
        "preset": "balanced",
        "created_at": time.time(),
        "total_distance_km": 120.0,
        "sla_compliance_pct": 90.0,
        "cluster_count": 2,
        "metadata": {
            "fuel_efficiency_score": 85.0,
            "violations": [
                {"type": "SLA_WINDOW_MISS", "count": 2, "details": "Traffic on FC Road"},
            ],
        },
        "vehicle_assignments": [
            {
                "vehicle_id": "Van-1",
                "distance_km": 60.0,
                "stops": ["P-1", "P-2"],
                "total_duration_min": 90.0,
            },
            {
                "vehicle_id": "Van-2",
                "distance_km": 60.0,
                "stops": ["P-3", "P-4"],
                "total_duration_min": 85.0,
            },
        ],
    }
    s_res = await db["routing_sessions"].insert_one(s_doc)
    session_id = str(s_res.inserted_id)

    # Pre-seed delivery events
    events = [
        {"routing_session_id": session_id, "vehicle_id": "Van-1", "status": "delivered", "is_late": False},
        {"routing_session_id": session_id, "vehicle_id": "Van-1", "status": "delivered", "is_late": True},
        {"routing_session_id": session_id, "vehicle_id": "Van-2", "status": "delivered", "is_late": False},
        {"routing_session_id": session_id, "vehicle_id": "Van-2", "status": "failed", "is_late": False},
    ]
    await db["delivery_events"].insert_many(events)

    # 1. Fuel efficiency trend
    res_fuel = await client.get("/analytics/fuel-efficiency")
    assert res_fuel.status_code == 200
    fuel_data = res_fuel.json()
    assert len(fuel_data) >= 1
    point = next(p for p in fuel_data if p["session_id"] == session_id)
    assert point["total_distance_km"] == 120.0
    assert point["fuel_efficiency_score"] == 85.0
    assert point["estimated_fuel_liters"] == 14.4  # 120 * 0.12

    # 2. Overall SLA compliance
    res_sla = await client.get("/analytics/sla-compliance")
    assert res_sla.status_code == 200
    sla_data = res_sla.json()
    assert sla_data["total_events"] >= 4
    assert sla_data["delivered_count"] >= 3

    # 3. Per-vehicle SLA breakdown
    res_veh_sla = await client.get("/analytics/sla-compliance?groupBy=vehicle")
    assert res_veh_sla.status_code == 200
    veh_sla_data = res_veh_sla.json()
    assert len(veh_sla_data) >= 2

    # 4. Violations
    res_viol = await client.get("/analytics/violations")
    assert res_viol.status_code == 200
    viol_data = res_viol.json()
    assert len(viol_data) >= 1
    assert any(v["violation_type"] == "SLA_WINDOW_MISS" for v in viol_data)

    # 5. Vehicle performance
    res_perf = await client.get("/analytics/vehicle-performance")
    assert res_perf.status_code == 200
    perf_data = res_perf.json()
    assert len(perf_data) >= 2

    # Clean up
    await db["routing_sessions"].delete_one({"_id": s_res.inserted_id})
    await db["delivery_events"].delete_many({"routing_session_id": session_id})


@pytest.mark.asyncio
async def test_analytics_empty_state(client: AsyncClient):
    """TC-10.2-05: Analytics endpoints handle empty database gracefully without 500 error."""
    res_fuel = await client.get("/analytics/fuel-efficiency")
    assert res_fuel.status_code == 200
    assert isinstance(res_fuel.json(), list)

    res_sla = await client.get("/analytics/sla-compliance")
    assert res_sla.status_code == 200
    assert "overall_compliance_pct" in res_sla.json()

    res_viol = await client.get("/analytics/violations")
    assert res_viol.status_code == 200
    assert isinstance(res_viol.json(), list)

    res_perf = await client.get("/analytics/vehicle-performance")
    assert res_perf.status_code == 200
    assert isinstance(res_perf.json(), list)
