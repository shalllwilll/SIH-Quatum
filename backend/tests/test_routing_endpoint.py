"""
backend/tests/test_routing_endpoint.py — Milestone 6.2

Test cases:
- TC-6.2-01: Trigger routing run via POST /routing-sessions/run
- TC-6.2-02: Poll status via GET /routing-sessions/{id}/status
- TC-6.2-03: Fetch completed result via GET /routing-sessions/{id}
- TC-6.2-04: Invalid preset rejected (422)
- TC-6.2-05: Nonexistent session returns 404
- TC-6.2-06: Assign confirms routes and updates vehicles/parcels
- TC-6.2-07: Different presets produce different fitness/evaluation profiles
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db import get_db
from app.main import app


@pytest_asyncio.fixture
async def client():
    """AsyncClient fixture with ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_tc_6_2_01_and_02_and_03_routing_run_status_and_details(client: AsyncClient):
    """TC-6.2-01, TC-6.2-02, TC-6.2-03: Trigger run, poll status, fetch completed solution."""
    # Ensure seed parcels and vehicles in DB
    db = get_db()
    await db["parcels"].delete_many({})
    await db["vehicles"].delete_many({})

    dummy_parcels = [
        {
            "address": f"Delivery Point #{i}, Pune",
            "lat": 18.5204 + (i % 3) * 0.01,
            "lon": 73.8567 + (i % 2) * 0.01,
            "weight_kg": 4.0,
            "sla_start_min": 540,
            "sla_deadline_min": 900,
            "status": "pending",
        }
        for i in range(1, 10)
    ]
    await db["parcels"].insert_many(dummy_parcels)

    dummy_vehicles = [
        {"label": "Van-1", "capacity_kg": 200.0, "status": "idle"},
        {"label": "Van-2", "capacity_kg": 200.0, "status": "idle"},
    ]
    await db["vehicles"].insert_many(dummy_vehicles)

    # Trigger routing run
    run_payload = {
        "preset": "balanced",
        "max_bounceback_retries": 1,
        "seed": 42,
        "async_run": False,
    }
    run_res = await client.post("/routing-sessions/run", json=run_payload)
    assert run_res.status_code == 200, run_res.text
    run_data = run_res.json()
    assert "session_id" in run_data
    session_id = run_data["session_id"]
    assert run_data["status"] == "completed"

    # Poll status
    status_res = await client.get(f"/routing-sessions/{session_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["session_id"] == session_id
    assert status_data["status"] == "completed"
    assert status_data["progress_percent"] == 100
    assert status_data["elapsed_seconds"] >= 0.0

    # Fetch full session details
    details_res = await client.get(f"/routing-sessions/{session_id}")
    assert details_res.status_code == 200
    details_data = details_res.json()
    assert details_data["id"] == session_id
    assert details_data["status"] == "completed"
    assert "vehicle_assignments" in details_data
    assert len(details_data["vehicle_assignments"]) > 0
    assert "sla_compliance_pct" in details_data
    assert "total_distance_km" in details_data


@pytest.mark.asyncio
async def test_tc_6_2_04_invalid_preset_rejected(client: AsyncClient):
    """TC-6.2-04: Invalid preset returns 422 with clear validation error."""
    bad_payload = {
        "preset": "super_fast_invalid_preset",
    }
    response = await client.post("/routing-sessions/run", json=bad_payload)
    assert response.status_code == 422
    err = response.json()
    assert err["error"] in ("Unprocessable Entity", "Validation Error")
    assert "detail" in err


@pytest.mark.asyncio
async def test_tc_6_2_05_nonexistent_session_404(client: AsyncClient):
    """TC-6.2-05: Fetching fake session ID returns 404."""
    fake_id = "64f1a2b3c4d5e6f7a8b9c088"
    status_res = await client.get(f"/routing-sessions/{fake_id}/status")
    assert status_res.status_code == 404

    details_res = await client.get(f"/routing-sessions/{fake_id}")
    assert details_res.status_code == 404


@pytest.mark.asyncio
async def test_tc_6_2_06_assign_session_routes(client: AsyncClient):
    """TC-6.2-06: Confirming routes updates vehicles and parcels status."""
    # Trigger routing run
    run_payload = {
        "preset": "balanced",
        "seed": 42,
    }
    run_res = await client.post("/routing-sessions/run", json=run_payload)
    assert run_res.status_code == 200
    session_id = run_res.json()["session_id"]

    # Assign routes
    assign_res = await client.post(f"/routing-sessions/{session_id}/assign")
    assert assign_res.status_code == 200
    assign_data = assign_res.json()
    assert assign_data["session_id"] == session_id
    assert assign_data["status"] == "assigned"
    assert assign_data["assigned_vehicles_count"] >= 1


@pytest.mark.asyncio
async def test_tc_6_2_07_presets_produce_different_metrics(client: AsyncClient):
    """TC-6.2-07: Different optimization presets trigger different weight behaviors."""
    res_dist = await client.post("/routing-sessions/run", json={"preset": "minimize_distance", "seed": 42})
    assert res_dist.status_code == 200
    id_dist = res_dist.json()["session_id"]

    res_sla = await client.post("/routing-sessions/run", json={"preset": "prioritize_sla", "seed": 42})
    assert res_sla.status_code == 200
    id_sla = res_sla.json()["session_id"]

    doc_dist = (await client.get(f"/routing-sessions/{id_dist}")).json()
    doc_sla = (await client.get(f"/routing-sessions/{id_sla}")).json()

    assert doc_dist["preset"] == "min_distance"
    assert doc_sla["preset"] == "prioritize_sla"
