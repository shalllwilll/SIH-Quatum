"""
Test suite for Milestone 0.3 — MongoDB connection & core schema stubs.

Test strategy:
  - TC-0.3-01 (DB connectivity)     → real MongoDB on localhost:27017
  - TC-0.3-02 (seed script)         → real MongoDB (inserts + verifies counts)
  - TC-0.3-03 (schema rejects bad parcel) → real MongoDB ($jsonSchema enforcement)
  - TC-0.3-04 (wrong-type rejected) → real MongoDB ($jsonSchema enforcement)
  - TC-0.3-05 (bad URI handled)     → no MongoDB needed (tests error path)
  - TC-0.3-06 (Pydantic round-trip) → mongomock (no real DB needed)

All real-DB tests use a dedicated test database ('logistics_test_0_3') that is
dropped before and after each test to guarantee isolation.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio

# Ensure MONGO_URI is available before importing app modules
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/logistics_test_0_3")

TEST_DB_NAME = "logistics_test_0_3"
REAL_MONGO_URI = f"mongodb://localhost:27017/{TEST_DB_NAME}"

# ---------------------------------------------------------------------------
# Fixture: real MongoDB client pointed at a clean test database
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def event_loop():
    """Use a single event loop for the whole module (avoids Motor task-group issues)."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def real_db():
    """
    Yield a fresh Motor database for each test, then drop it.
    Skips if port 27017 is not reachable.
    """
    import socket
    try:
        s = socket.create_connection(("localhost", 27017), timeout=1)
        s.close()
    except OSError:
        pytest.skip("MongoDB not available on localhost:27017 — skipping live DB test.")

    from motor.motor_asyncio import AsyncIOMotorClient

    from app.db import apply_collection_validators

    client = AsyncIOMotorClient(REAL_MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client[TEST_DB_NAME]

    # Clean slate before test
    await client.drop_database(TEST_DB_NAME)
    await apply_collection_validators(db)

    yield db

    # Teardown
    await client.drop_database(TEST_DB_NAME)
    client.close()


# ---------------------------------------------------------------------------
# TC-0.3-01 — DB connects successfully → /health/db returns 200
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ping_db_success(real_db):
    """TC-0.3-01: ping_db() returns True when MongoDB is reachable."""
    # Override module-level db singleton to point at test DB
    os.environ["MONGO_URI"] = REAL_MONGO_URI

    from app.db import ping_db, reset_client
    reset_client()  # force re-creation with test URI

    result = await ping_db()
    assert result is True, "ping_db() should return True on successful connection"

    reset_client()  # clean up singleton for other tests


@pytest.mark.asyncio
async def test_health_db_endpoint(real_db):
    """TC-0.3-01 (endpoint): GET /health/db returns 200 with connected status."""
    import socket
    try:
        s = socket.create_connection(("localhost", 27017), timeout=1)
        s.close()
    except OSError:
        pytest.skip("MongoDB not available — skipping health/db endpoint test.")

    os.environ["MONGO_URI"] = REAL_MONGO_URI
    from app.db import reset_client
    reset_client()

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/health/db")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["db"] == "connected"

    reset_client()


# ---------------------------------------------------------------------------
# TC-0.3-02 — Seed script inserts expected records
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_seed_dev_data_inserts_records(real_db):
    """TC-0.3-02: seed_dev_data.py inserts 1 warehouse, 2 parcels, 1 vehicle."""
    os.environ["MONGO_URI"] = REAL_MONGO_URI

    # Import and run the seed function directly against the test DB
    ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(ROOT))

    from backend.scripts.seed_dev_data import seed
    counts = await seed(db_override=TEST_DB_NAME)

    assert counts["warehouses"] == 1, "Expected 1 warehouse document"
    assert counts["parcels"] == 2, "Expected 2 parcel documents"
    assert counts["vehicles"] == 1, "Expected 1 vehicle document"

    # Verify actual DB counts
    wh_count = await real_db["warehouses"].count_documents({})
    p_count = await real_db["parcels"].count_documents({})
    v_count = await real_db["vehicles"].count_documents({})

    assert wh_count == 1
    assert p_count == 2
    assert v_count == 1


@pytest.mark.asyncio
async def test_seed_idempotent(real_db):
    """TC-0.3-02 (idempotency): Running seed twice produces same counts (drop+reseed)."""
    os.environ["MONGO_URI"] = REAL_MONGO_URI

    ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(ROOT))

    from backend.scripts.seed_dev_data import seed

    await seed(db_override=TEST_DB_NAME)
    counts2 = await seed(db_override=TEST_DB_NAME)  # second run

    assert counts2["warehouses"] == 1
    assert counts2["parcels"] == 2
    assert counts2["vehicles"] == 1


# ---------------------------------------------------------------------------
# TC-0.3-03 — Schema validation rejects parcel missing sla_deadline_min
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schema_rejects_parcel_missing_required_field(real_db):
    """TC-0.3-03: Inserting a parcel without sla_deadline_min is rejected by MongoDB."""
    from pymongo.errors import WriteError

    bad_parcel = {
        "address": "Missing Field St",
        "lat": 18.52,
        "lon": 73.85,
        "weight_kg": 5.0,
        "sla_start_min": 480,
        # sla_deadline_min deliberately MISSING
        "status": "pending",
    }

    with pytest.raises(WriteError) as exc_info:
        await real_db["parcels"].insert_one(bad_parcel)

    assert exc_info.value is not None, (
        "MongoDB $jsonSchema should reject a parcel missing 'sla_deadline_min'"
    )


# ---------------------------------------------------------------------------
# TC-0.3-04 — Schema validation rejects wrong-type field
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schema_rejects_wrong_type_field(real_db):
    """TC-0.3-04: Inserting a parcel with weight_kg as string is rejected by MongoDB."""
    from pymongo.errors import WriteError

    bad_parcel = {
        "address": "Wrong Type Road",
        "lat": 18.52,
        "lon": 73.85,
        "weight_kg": "heavy",    # STRING — should be double/int
        "sla_start_min": 480,
        "sla_deadline_min": 720,
        "status": "pending",
    }

    with pytest.raises(WriteError) as exc_info:
        await real_db["parcels"].insert_one(bad_parcel)

    assert exc_info.value is not None, (
        "MongoDB $jsonSchema should reject 'weight_kg' when it is a string"
    )


# ---------------------------------------------------------------------------
# TC-0.3-05 — Connection failure handled with clear error (no real DB needed)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bad_uri_raises_clear_error():
    """TC-0.3-05: ping_db() with an invalid URI raises RuntimeError, not a raw traceback."""
    from app.db import reset_client

    original_uri = os.environ.get("MONGO_URI")
    os.environ["MONGO_URI"] = "mongodb://localhost:19999/bad_db"  # Nothing on this port
    reset_client()

    from app.db import ping_db

    with pytest.raises(RuntimeError) as exc_info:
        await ping_db()

    error_msg = str(exc_info.value)
    assert "MongoDB connectivity check failed" in error_msg, (
        f"Error message should be descriptive, got: {error_msg}"
    )

    # Restore
    if original_uri:
        os.environ["MONGO_URI"] = original_uri
    reset_client()


# ---------------------------------------------------------------------------
# TC-0.3-06 — Pydantic model round-trips to Mongo doc — units unchanged
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pydantic_roundtrip_parcel(real_db):
    """TC-0.3-06: Pydantic Parcel model round-trips to/from MongoDB with fields intact."""
    from app.models.parcel import Parcel, ParcelCreate

    original = ParcelCreate(
        address="42 Round-Trip Lane, Pune",
        lat=18.5200,
        lon=73.8560,
        node_id=None,
        weight_kg=4.5,
        sla_start_min=540,   # 09:00
        sla_deadline_min=780,  # 13:00
        status="pending",
    )

    # Insert via model dict (exclude unset optional fields)
    doc = original.model_dump(exclude_none=True)
    result = await real_db["parcels"].insert_one(doc)

    # Fetch raw document back
    raw = await real_db["parcels"].find_one({"_id": result.inserted_id})
    assert raw is not None

    # Verify canonical unit fields are ints, not display strings
    assert isinstance(raw["sla_start_min"], int), "sla_start_min must be stored as int"
    assert isinstance(raw["sla_deadline_min"], int), "sla_deadline_min must be stored as int"
    assert isinstance(raw["weight_kg"], float), "weight_kg must be stored as float"

    # Values must match exactly — no coercion or reformatting
    assert raw["sla_start_min"] == 540
    assert raw["sla_deadline_min"] == 780
    assert abs(raw["weight_kg"] - 4.5) < 1e-9

    # Pydantic can reconstruct from raw doc cleanly
    raw["_id"] = str(raw["_id"])
    reconstructed = Parcel.model_validate(raw)
    assert reconstructed.sla_start_min == original.sla_start_min
    assert reconstructed.sla_deadline_min == original.sla_deadline_min
    assert abs(reconstructed.weight_kg - original.weight_kg) < 1e-9
