"""
backend/tests/test_api_crud.py — Milestone 6.1

Test cases:
- TC-6.1-01: Create warehouse via POST /warehouses
- TC-6.1-02: List parcels paginated via GET /parcels
- TC-6.1-03: Invalid parcel payload rejected (422)
- TC-6.1-04: Nonexistent resource returns 404 with consistent error body
- TC-6.1-05: Vehicle status update via PATCH /vehicles/{id}
- TC-6.1-06: CORS header validation for allowed vs disallowed origins
- TC-6.1-07: Canonical units remain typed ints/floats end-to-end
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
async def test_tc_6_1_01_create_warehouse(client: AsyncClient):
    """TC-6.1-01: POST /warehouses creates and persists a warehouse."""
    payload = {
        "name": "Test Kothrud Depot",
        "lat": 18.5074,
        "lon": 73.8077,
        "address": "Paud Road, Kothrud, Pune",
        "node_id": 12345678,
    }

    response = await client.post("/warehouses", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()

    assert "id" in data
    assert data["id"] is not None
    assert data["name"] == payload["name"]
    assert data["lat"] == payload["lat"]
    assert data["lon"] == payload["lon"]
    assert data["address"] == payload["address"]
    assert data["node_id"] == payload["node_id"]

    # Verify fetch by ID
    get_res = await client.get(f"/warehouses/{data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == payload["name"]


@pytest.mark.asyncio
async def test_tc_6_1_02_list_parcels_paginated(client: AsyncClient):
    """TC-6.1-02: GET /parcels supports pagination and metadata."""
    # Ensure at least 25 parcels in database
    db = get_db()
    current_count = await db["parcels"].count_documents({})
    if current_count < 25:
        dummy_parcels = [
            {
                "address": f"Stop #{i}, Pune",
                "lat": 18.5204 + i * 0.001,
                "lon": 73.8567 + i * 0.001,
                "weight_kg": 2.5,
                "sla_start_min": 540,
                "sla_deadline_min": 720,
                "status": "pending",
            }
            for i in range(30)
        ]
        await db["parcels"].insert_many(dummy_parcels)

    response = await client.get("/parcels?page=1&limit=20")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "pages" in data

    assert len(data["items"]) == 20
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total"] >= 20
    assert data["pages"] >= 1


@pytest.mark.asyncio
async def test_tc_6_1_03_invalid_parcel_rejected(client: AsyncClient):
    """TC-6.1-03: POST /parcels missing required fields or with invalid SLA returns 422."""
    # Missing required sla_deadline_min
    bad_payload = {
        "address": "Invalid Stop, Pune",
        "lat": 18.52,
        "lon": 73.85,
        "weight_kg": 5.0,
        "sla_start_min": 540,
    }
    response = await client.post("/parcels", json=bad_payload)
    assert response.status_code == 422
    err = response.json()
    assert err["error"] == "Validation Error"
    assert "detail" in err

    # Invalid SLA window (deadline <= start)
    inverted_sla = {
        "address": "Invalid SLA Stop, Pune",
        "lat": 18.52,
        "lon": 73.85,
        "weight_kg": 5.0,
        "sla_start_min": 600,
        "sla_deadline_min": 500,  # Invalid
    }
    response_sla = await client.post("/parcels", json=inverted_sla)
    assert response_sla.status_code == 422


@pytest.mark.asyncio
async def test_tc_6_1_04_nonexistent_resource_404(client: AsyncClient):
    """TC-6.1-04: Nonexistent resource returns 404 with standard error body."""
    fake_id = "64f1a2b3c4d5e6f7a8b9c099"
    response = await client.get(f"/vehicles/{fake_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "Not Found"
    assert "detail" in data

    # Invalid hex ObjectId string
    invalid_hex_res = await client.get("/vehicles/invalid-id-format")
    assert invalid_hex_res.status_code == 404


@pytest.mark.asyncio
async def test_tc_6_1_05_vehicle_crud_and_patch(client: AsyncClient):
    """TC-6.1-05: Create and PATCH vehicle status."""
    # Create vehicle
    create_payload = {
        "label": "Van-Test-Patch",
        "capacity_kg": 350.0,
        "status": "idle",
    }
    res = await client.post("/vehicles", json=create_payload)
    assert res.status_code == 201
    vehicle = res.json()
    vehicle_id = vehicle["id"]

    # PATCH vehicle to en_route with driver_id
    patch_payload = {
        "status": "en_route",
        "driver_id": "driver_alpha",
    }
    patch_res = await client.patch(f"/vehicles/{vehicle_id}", json=patch_payload)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["status"] == "en_route"
    assert updated["driver_id"] == "driver_alpha"

    # Re-fetch vehicle to verify persistence
    get_res = await client.get(f"/vehicles/{vehicle_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "en_route"


@pytest.mark.asyncio
async def test_tc_6_1_06_cors_headers(client: AsyncClient):
    """TC-6.1-06: CORS headers present for allowed origins and absent/blocked for unknown origins."""
    # Allowed origin: Admin frontend (5173)
    allowed_origin = "http://localhost:5173"
    res_allowed = await client.options(
        "/warehouses",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_allowed.headers.get("access-control-allow-origin") == allowed_origin

    # Disallowed origin
    disallowed_origin = "http://malicious-site.com"
    res_disallowed = await client.options(
        "/warehouses",
        headers={
            "Origin": disallowed_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_disallowed.headers.get("access-control-allow-origin") != disallowed_origin


@pytest.mark.asyncio
async def test_tc_6_1_07_canonical_units_end_to_end(client: AsyncClient):
    """TC-6.1-07: Parcel SLA deadlines and weights remain strictly typed ints and floats."""
    payload = {
        "address": "Canonical Unit Check Stop",
        "lat": 18.5204,
        "lon": 73.8567,
        "weight_kg": 12.75,
        "sla_start_min": 600,
        "sla_deadline_min": 840,
        "status": "pending",
    }
    create_res = await client.post("/parcels", json=payload)
    assert create_res.status_code == 201
    created_id = create_res.json()["id"]

    get_res = await client.get(f"/parcels/{created_id}")
    assert get_res.status_code == 200
    parcel = get_res.json()

    # Verify types are preserved as int/float, not converted to display strings
    assert isinstance(parcel["sla_start_min"], int)
    assert parcel["sla_start_min"] == 600
    assert isinstance(parcel["sla_deadline_min"], int)
    assert parcel["sla_deadline_min"] == 840
    assert isinstance(parcel["weight_kg"], (int, float))
    assert parcel["weight_kg"] == 12.75
