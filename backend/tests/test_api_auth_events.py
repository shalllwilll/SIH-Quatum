"""
backend/tests/test_api_auth_events.py — Milestone 6.3

Test cases:
- TC-6.3-01: Admin login succeeds with token
- TC-6.3-02: Wrong password rejected (401)
- TC-6.3-03: Driver role cannot access admin-protected routes (403)
- TC-6.3-04: Bulk vehicle positions returned (GET /vehicles/positions)
- TC-6.3-05: Delivery event recorded and parcel status updated (POST /delivery-events)
- TC-6.3-06: Nonexistent parcel rejected (404)
- TC-6.3-07: Driver manifest data isolation (driver sees only own vehicle/manifest)
"""

from __future__ import annotations

from typing import Annotated, Any

import pytest
import pytest_asyncio
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from app.auth.middleware import require_admin
from app.db import get_db
from app.main import app


@pytest_asyncio.fixture
async def client():
    """AsyncClient fixture with ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_tc_6_3_01_admin_login_success(client: AsyncClient):
    """TC-6.3-01: Valid admin credentials return token and user profile."""
    payload = {"username": "admin", "password": "admin123"}
    res = await client.post("/auth/login", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"

    # Verify GET /auth/me with Bearer token
    token = data["access_token"]
    me_res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_tc_6_3_02_wrong_password_rejected(client: AsyncClient):
    """TC-6.3-02: Invalid credentials return 401 Unauthorized."""
    bad_payload = {"username": "admin", "password": "wrong_password_xyz"}
    res = await client.post("/auth/login", json=bad_payload)
    assert res.status_code == 401
    assert "detail" in res.json()

    bad_user = {"username": "nonexistent_user", "password": "any"}
    res2 = await client.post("/auth/login", json=bad_user)
    assert res2.status_code == 401


@pytest.mark.asyncio
async def test_tc_6_3_03_driver_cannot_access_admin_route(client: AsyncClient):
    """TC-6.3-03: Driver token receives 403 Forbidden on admin-protected endpoints."""
    # Temporarily mount a test admin-only route
    @app.get("/test-admin-only-gate", tags=["Test"])
    async def _test_admin_gate(_user: Annotated[dict[str, Any], Depends(require_admin)]):
        return {"status": "admin_granted"}

    # Login as driver1
    driver_login = await client.post("/auth/login", json={"username": "driver1", "password": "driver123"})
    assert driver_login.status_code == 200
    driver_token = driver_login.json()["access_token"]

    # Attempt calling admin-only gate with driver token
    res = await client.get("/test-admin-only-gate", headers={"Authorization": f"Bearer {driver_token}"})
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]

    # Attempt calling admin-only gate with admin token
    admin_login = await client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = admin_login.json()["access_token"]
    admin_res = await client.get("/test-admin-only-gate", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    assert admin_res.json()["status"] == "admin_granted"


@pytest.mark.asyncio
async def test_tc_6_3_04_bulk_vehicle_positions(client: AsyncClient):
    """TC-6.3-04: GET /vehicles/positions returns live positions for all active vehicles."""
    db = get_db()
    # Insert test vehicles
    await db["vehicles"].delete_many({})
    await db["vehicles"].insert_many([
        {"label": "Van-1", "capacity_kg": 250.0, "status": "en_route", "driver_id": "driver1"},
        {"label": "Van-2", "capacity_kg": 250.0, "status": "idle", "driver_id": "driver2"},
    ])

    res = await client.get("/vehicles/positions")
    assert res.status_code == 200
    positions = res.json()
    assert len(positions) >= 2
    for pos in positions:
        assert "vehicle_id" in pos
        assert "lat" in pos
        assert "lon" in pos
        assert "speed_kmh" in pos
        assert "heading_deg" in pos
        assert "status" in pos


@pytest.mark.asyncio
async def test_tc_6_3_05_and_06_delivery_event_recording(client: AsyncClient):
    """TC-6.3-05 & TC-6.3-06: Record delivery outcome and reject nonexistent parcel."""
    db = get_db()
    # Create parcel in DB
    parcel_res = await db["parcels"].insert_one({
        "address": "Koregaon Park North Main Rd, Pune",
        "lat": 18.5362,
        "lon": 73.8940,
        "weight_kg": 6.0,
        "sla_start_min": 600,
        "sla_deadline_min": 780,
        "status": "en_route",
    })
    parcel_id = str(parcel_res.inserted_id)

    event_payload = {
        "routing_session_id": "64f1a2b3c4d5e6f7a8b9c099",
        "vehicle_id": "Van-1",
        "parcel_id": parcel_id,
        "status": "delivered",
        "recorded_at_min": 645,
        "note": "Delivered to security desk",
    }

    # Record event
    res = await client.post("/delivery-events", json=event_payload)
    assert res.status_code == 201, res.text
    event_data = res.json()
    assert event_data["status"] == "delivered"
    assert event_data["parcel_id"] == parcel_id
    assert event_data["recorded_at_min"] == 645

    # Check parcel status updated in database
    updated_parcel = await db["parcels"].find_one({"_id": parcel_res.inserted_id})
    assert updated_parcel["status"] == "delivered"

    # Query events list
    list_res = await client.get(f"/delivery-events?parcel_id={parcel_id}")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # TC-6.3-06: Nonexistent parcel rejected
    bad_event = {
        "routing_session_id": "64f1a2b3c4d5e6f7a8b9c099",
        "vehicle_id": "Van-1",
        "parcel_id": "64f1a2b3c4d5e6f7a8b9c999",  # Fake parcel ID
        "status": "delivered",
        "recorded_at_min": 650,
    }
    bad_res = await client.post("/delivery-events", json=bad_event)
    assert bad_res.status_code == 404


@pytest.mark.asyncio
async def test_tc_6_3_07_driver_manifest_data_isolation(client: AsyncClient):
    """TC-6.3-07: Driver A polls manifest and sees only Driver A's assigned vehicle and stops."""
    # Login Driver 1
    d1_res = await client.post("/auth/login", json={"username": "driver1", "password": "driver123"})
    token_d1 = d1_res.json()["access_token"]

    # Login Driver 2
    d2_res = await client.post("/auth/login", json={"username": "driver2", "password": "driver223"})
    token_d2 = d2_res.json()["access_token"]

    # Driver 1 queries manifest
    res1 = await client.get("/driver/manifest", headers={"Authorization": f"Bearer {token_d1}"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["driver_id"] == "driver1"
    assert data1["vehicle_label"] == "Van-1"

    # Driver 2 queries manifest
    res2 = await client.get("/driver/manifest", headers={"Authorization": f"Bearer {token_d2}"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["driver_id"] == "driver2"
    assert data2["vehicle_label"] == "Van-2"

    # Driver 1 cannot see Driver 2's vehicle assignment
    assert data1["vehicle_label"] != data2["vehicle_label"]
