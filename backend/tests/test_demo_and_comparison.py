"""
backend/tests/test_demo_and_comparison.py — Tests for Demo Scenario & Preset Comparison

Verifies:
- TC-DEMO-01: Seeding realistic Pune clustered demo scenarios
- TC-DEMO-02: Injecting and clearing simulated TomTom traffic bottlenecks
- TC-COMPARE-01: Multi-preset comparison endpoint returning differentiated tradeoffs
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_tc_demo_01_seed_scenario():
    """Verify demo scenario generator seeds clustered parcels across 3 hubs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/demo/seed-scenario",
            json={
                "num_parcels": 24,
                "selected_warehouse": "all",
                "vehicle_count": 3,
                "vehicle_capacity_kg": 200.0,
                "seed": 42,
            },
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["status"] == "ok"
        assert data["parcels_created"] == 24
        assert data["vehicles_active"] == 3
        assert data["warehouses_active"] >= 3
        assert "WH-PUNE-001" in data["warehouse_distribution"]
        assert "WH-PUNE-002" in data["warehouse_distribution"]
        assert "WH-PUNE-003" in data["warehouse_distribution"]
        assert len(data["sample_stops"]) > 0


@pytest.mark.asyncio
async def test_tc_demo_02_inject_and_clear_traffic_spike():
    """Verify traffic disturbance injection updates traffic cache in real-time."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Inject bottleneck at Pune Station
        res_inject = await client.post(
            "/demo/inject-traffic-spike",
            json={
                "corridor_key": "pune_station",
                "active": True,
                "severity": 2.8,
            },
        )
        assert res_inject.status_code == 200, res_inject.text
        data_inject = res_inject.json()
        assert data_inject["status"] == "ok"
        assert data_inject["segment_id"] == "SEG-039"
        assert data_inject["congestion_ratio"] == 2.8
        assert data_inject["source"] == "simulated_disturbance"

        # Verify through /traffic/status
        res_status = await client.get("/traffic/status")
        assert res_status.status_code == 200
        status_data = res_status.json()
        # Find SEG-039 if in sample
        for seg in status_data.get("sample_segments", []):
            if seg["segment_id"] == "SEG-039":
                assert seg["congestion_ratio"] == 2.8

        # 2. Clear disturbance
        res_clear = await client.post(
            "/demo/inject-traffic-spike",
            json={
                "corridor_key": "reset",
                "active": False,
            },
        )
        assert res_clear.status_code == 200
        data_clear = res_clear.json()
        assert data_clear["status"] == "ok"
        assert data_clear["congestion_ratio"] == 1.0


@pytest.mark.asyncio
async def test_tc_compare_01_presets_differentiation():
    """Verify side-by-side comparison endpoint returns differentiated metrics."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/routing-sessions/compare",
            json={"seed": 42},
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["status"] == "ok"
        assert "presets" in data
        presets = data["presets"]

        # Ensure all 4 presets are returned
        assert "balanced" in presets
        assert "min_distance" in presets
        assert "prioritize_sla" in presets
        assert "min_fuel" in presets

        bal = presets["balanced"]
        dist = presets["min_distance"]
        sla = presets["prioritize_sla"]
        fuel = presets["min_fuel"]

        # Verify SLA priorities
        assert sla["sla_compliance_pct"] == 100.0
        assert sla["sla_violations_count"] == 0

        # Verify distance priorities: Min Distance has lower km than Balanced
        assert dist["total_distance_km"] < bal["total_distance_km"]

        # Verify fuel priorities: Min Fuel has lower or equal fuel than Balanced
        assert fuel["estimated_fuel_litres"] < bal["estimated_fuel_litres"]

        # Weights check
        assert bal["weights"]["w1_distance"] == 0.25
        assert dist["weights"]["w1_distance"] == 0.50
        assert sla["weights"]["w4_sla"] == 0.50

        # Tradeoff summary check
        assert len(data["tradeoff_summary"]) >= 2
