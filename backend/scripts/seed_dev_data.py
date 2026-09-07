"""
backend/scripts/seed_dev_data.py — Milestone 0.3

Inserts minimal dummy data into the dev database for connectivity and schema
testing ONLY. This is NOT the real Pune dataset (that comes in Phase 1/Milestone 1.2).

Data seeded:
  - 1 dummy warehouse
  - 2 dummy parcels
  - 1 dummy vehicle

Idempotent behaviour:
  Running this script on a DB that already has seed data will DROP and re-seed
  the three collections (warehouses, parcels, vehicles) cleanly. This is safe
  since it is dev-only dummy data.

Usage (from repo root):
    python -m backend.scripts.seed_dev_data
  or:
    backend/.venv/bin/python -m backend.scripts.seed_dev_data
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Ensure backend package is importable when run as a script
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

# Load .env before importing db module
env_path = ROOT / "backend" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    print("ERROR: MONGO_URI environment variable is not set.", file=sys.stderr)
    print("Copy backend/.env.example to backend/.env and configure it.", file=sys.stderr)
    sys.exit(1)

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

# ---------------------------------------------------------------------------
# Dummy data — units follow spec §3a strictly:
#   times = int (minutes since midnight), distances = float (km)
# ---------------------------------------------------------------------------

DUMMY_WAREHOUSE = {
    "name": "Dev Warehouse Alpha",
    "lat": 18.5204,   # Pune city centre (dummy coords)
    "lon": 73.8567,
    "address": "1 Dev Lane, Pune (dummy)",
    "node_id": None,  # graph snap happens in Phase 1
}

DUMMY_PARCELS = [
    {
        "address": "42 Test Street, Pune (dummy)",
        "lat": 18.5120,
        "lon": 73.8450,
        "node_id": None,
        "weight_kg": 3.5,
        "sla_start_min": 480,    # 08:00
        "sla_deadline_min": 720, # 12:00
        "status": "pending",
    },
    {
        "address": "7 Sample Road, Pune (dummy)",
        "lat": 18.5300,
        "lon": 73.8680,
        "node_id": None,
        "weight_kg": 7.2,
        "sla_start_min": 600,    # 10:00
        "sla_deadline_min": 840, # 14:00
        "status": "pending",
    },
]

DUMMY_VEHICLE = {
    "label": "Dev-Van-1",
    "capacity_kg": 100.0,
    "status": "idle",
    "driver_id": None,
    "current_warehouse_id": None,
}


async def seed(db_override: str | None = None) -> dict[str, int]:
    """
    Drop and re-seed dev collections.

    Args:
        db_override: If provided, seed this database name instead of the default.

    Returns:
        Dict with counts of inserted documents per collection.
    """
    client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    try:
        # Resolve DB name
        if db_override:
            db_name = db_override
        else:
            uri_path = MONGO_URI.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
            db_name = uri_path if uri_path else "logistics_db"

        db = client[db_name]

        # Verify connectivity
        await client.admin.command("ping")
        print(f"Connected to MongoDB. Seeding database: '{db_name}'")

        # Drop existing dev-seed data to ensure idempotency
        for col in ("warehouses", "parcels", "vehicles"):
            await db[col].drop()
            print(f"  Dropped collection '{col}'.")

        # Re-apply validators after drop (drop removes them)
        from app.db import apply_collection_validators
        await apply_collection_validators(db)
        print("  $jsonSchema validators re-applied.")

        # Insert seed data
        wh_result = await db["warehouses"].insert_one(DUMMY_WAREHOUSE.copy())
        print(f"  Inserted 1 warehouse (_id={wh_result.inserted_id}).")

        parcel_result = await db["parcels"].insert_many(
            [p.copy() for p in DUMMY_PARCELS]
        )
        print(f"  Inserted {len(parcel_result.inserted_ids)} parcels.")

        veh_result = await db["vehicles"].insert_one(DUMMY_VEHICLE.copy())
        print(f"  Inserted 1 vehicle (_id={veh_result.inserted_id}).")

        print("Seed complete.")
        return {
            "warehouses": 1,
            "parcels": len(parcel_result.inserted_ids),
            "vehicles": 1,
        }

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed())
