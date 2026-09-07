"""
MongoDB connection singleton and collection schema setup — Milestone 0.3.

Design decisions (recorded per playbook):
- Driver: Motor (async) — chosen for consistency with Phase 9's async polling endpoints.
- Unit rule (spec §3a): all time values as int (minutes since midnight); all distances as
  float (km). Enforced at both Pydantic and $jsonSchema levels.
- congestion_type is stored as a string enum ("multiplicative" | "additive"), never bool.

Usage:
    from app.db import get_db, ping_db

    db = get_db()
    parcels_col = db["parcels"]
"""

from __future__ import annotations

import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level client — created once at import time.
# The actual network connection is deferred until the first operation.
# ---------------------------------------------------------------------------

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def _make_client() -> AsyncIOMotorClient:
    """Build and return a Motor client from the MONGO_URI env var."""
    uri = os.environ.get("MONGO_URI")
    if not uri:
        raise RuntimeError(
            "MONGO_URI environment variable is not set. "
            "Copy backend/.env.example to backend/.env and configure it."
        )
    return AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)


def get_client() -> AsyncIOMotorClient:
    """Return the shared Motor client, creating it if necessary."""
    global _client
    if _client is None:
        _client = _make_client()
    return _client


def get_db(db_name: str | None = None) -> AsyncIOMotorDatabase:
    """
    Return the shared Motor database handle.

    Args:
        db_name: Override database name (useful in tests). Defaults to the
                 database portion of MONGO_URI, falling back to 'logistics_db'.
    """
    global _db
    if _db is None or db_name is not None:
        client = get_client()
        if db_name:
            return client[db_name]
        # Extract DB name from URI, fall back to 'logistics_db'
        uri = os.environ.get("MONGO_URI", "")
        parsed_db = uri.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
        resolved_name = parsed_db if parsed_db else "logistics_db"
        _db = client[resolved_name]
    return _db


async def ping_db() -> bool:
    """
    Send a lightweight ping to the MongoDB server.

    Returns True on success, raises RuntimeError with a descriptive message on failure.
    This is used by the /health/db endpoint and startup verification.
    """
    try:
        client = get_client()
        await client.admin.command("ping")
        return True
    except Exception as exc:
        raise RuntimeError(
            f"MongoDB connectivity check failed: {exc}. "
            "Verify MONGO_URI in your .env file and that the MongoDB server is reachable."
        ) from exc


def reset_client() -> None:
    """
    Close and reset the Motor client. Used in tests to swap databases.
    """
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


# ---------------------------------------------------------------------------
# MongoDB $jsonSchema collection validators
# Enforces required fields and canonical types at the database layer.
# Mirrors the Pydantic models but acts as a last-line-of-defence constraint.
# ---------------------------------------------------------------------------

_COLLECTION_VALIDATORS: dict[str, dict] = {
    "warehouses": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "lat", "lon", "address"],
            "properties": {
                "name": {"bsonType": "string"},
                "lat": {"bsonType": "double"},
                "lon": {"bsonType": "double"},
                "address": {"bsonType": "string"},
                "node_id": {"bsonType": ["int", "long", "null"]},
            },
        }
    },
    "parcels": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "address",
                "lat",
                "lon",
                "weight_kg",
                "sla_start_min",
                "sla_deadline_min",
                "status",
            ],
            "properties": {
                "address": {"bsonType": "string"},
                "lat": {"bsonType": "double"},
                "lon": {"bsonType": "double"},
                "node_id": {"bsonType": ["int", "long", "null"]},
                # weight_kg must be a positive number
                "weight_kg": {"bsonType": ["double", "int"], "minimum": 0},
                # SLA fields stored as int minutes-since-midnight (spec §3a)
                "sla_start_min": {"bsonType": "int", "minimum": 0, "maximum": 1439},
                "sla_deadline_min": {"bsonType": "int", "minimum": 0, "maximum": 1439},
                "status": {
                    "bsonType": "string",
                    "enum": ["pending", "assigned", "en_route", "delivered", "failed"],
                },
            },
        }
    },
    "vehicles": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["label", "capacity_kg", "status"],
            "properties": {
                "label": {"bsonType": "string"},
                "capacity_kg": {"bsonType": ["double", "int"], "minimum": 0},
                "status": {
                    "bsonType": "string",
                    "enum": ["idle", "en_route", "delivering", "complete"],
                },
                "driver_id": {"bsonType": ["string", "null"]},
                "current_warehouse_id": {"bsonType": ["string", "null"]},
            },
        }
    },
    "routing_sessions": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["preset", "status", "created_at"],
            "properties": {
                "preset": {
                    "bsonType": "string",
                    "enum": ["balanced", "min_distance", "min_fuel", "prioritize_sla"],
                },
                "status": {
                    "bsonType": "string",
                    "enum": ["pending", "running", "completed", "failed"],
                },
                "created_at": {"bsonType": ["double", "int"]},
                "cluster_count": {"bsonType": ["int", "null"]},
                "vehicle_assignments": {"bsonType": "array"},
                "fitness_history": {"bsonType": "array"},
                "seeded": {"bsonType": "bool"},
            },
        }
    },
    "delivery_events": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "routing_session_id",
                "vehicle_id",
                "parcel_id",
                "status",
                "recorded_at_min",
                "recorded_at_wall",
            ],
            "properties": {
                "routing_session_id": {"bsonType": "string"},
                "vehicle_id": {"bsonType": "string"},
                "parcel_id": {"bsonType": "string"},
                "status": {"bsonType": "string", "enum": ["delivered", "failed"]},
                # recorded_at_min: int minutes since midnight (spec §3a)
                "recorded_at_min": {"bsonType": "int", "minimum": 0, "maximum": 1439},
                "recorded_at_wall": {"bsonType": ["double", "int"]},
                "note": {"bsonType": ["string", "null"]},
            },
        }
    },
}


async def apply_collection_validators(db: AsyncIOMotorDatabase | None = None) -> None:
    """
    Create all five core collections (if absent) and apply $jsonSchema validators.

    Idempotent: if a collection already exists, the validator is updated via
    `collMod` rather than re-created. Safe to call on every startup.

    Args:
        db: Database handle to apply validators on. Defaults to get_db().
    """
    target_db = db if db is not None else get_db()
    existing_collections = await target_db.list_collection_names()

    for collection_name, validator in _COLLECTION_VALIDATORS.items():
        if collection_name not in existing_collections:
            logger.info("Creating collection '%s' with $jsonSchema validator.", collection_name)
            await target_db.create_collection(
                collection_name,
                validator=validator,
                validationAction="error",   # reject invalid documents (not just warn)
                validationLevel="strict",   # validate on insert AND update
            )
        else:
            logger.info("Updating validator for existing collection '%s'.", collection_name)
            await target_db.command(
                "collMod",
                collection_name,
                validator=validator,
                validationAction="error",
                validationLevel="strict",
            )
