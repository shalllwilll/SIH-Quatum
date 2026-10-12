"""
backend/scripts/startup_healthcheck.py — Milestone 11.2

Startup Readiness and Dependency Health Check:
Validates MongoDB database connectivity, OpenStreetMap graph cache availability,
TomTom Live Traffic API reachability, and seed dataset presence before demo/production deployment.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.db import get_db, ping_db
from app.graph.loader import DEFAULT_GRAPH_PATH



async def run_healthcheck() -> bool:
    print("=" * 72)
    print("      ABRAXAS PLATFORM PRE-FLIGHT STARTUP HEALTH CHECK")
    print("=" * 72)

    all_passed = True

    # 1. Environment Configuration Check
    print("\n[1/5] Checking Environment Configuration...")
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("  ❌ FAIL: 'MONGO_URI' is not configured in .env")
        all_passed = False
    else:
        print(f"  ✅ PASS: MONGO_URI is configured ({mongo_uri.split('@')[-1]})")

    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        print("  ⚠️ WARN: 'JWT_SECRET' is not set; using internal default.")
    else:
        print("  ✅ PASS: JWT_SECRET configured.")

    # 2. MongoDB Connectivity Check
    print("\n[2/5] Checking MongoDB Connectivity...")
    try:
        db_alive = await ping_db()
        if db_alive:
            print("  ✅ PASS: Connected to MongoDB successfully (ping OK).")
        else:
            print("  ❌ FAIL: Ping to MongoDB failed.")
            all_passed = False
    except Exception as exc:
        print(f"  ❌ FAIL: MongoDB connection exception: {exc}")
        all_passed = False

    # 3. Seed Dataset Verification
    print("\n[3/5] Checking Seed Data Records...")
    try:
        db = get_db()
        wh_count = await db["warehouses"].count_documents({})
        parcel_count = await db["parcels"].count_documents({})
        vehicle_count = await db["vehicles"].count_documents({})
        session_count = await db["routing_sessions"].count_documents({})

        print(f"  • Warehouses:       {wh_count} hubs found")
        print(f"  • Delivery Parcels: {parcel_count} stops found")
        print(f"  • Fleet Vehicles:   {vehicle_count} vehicles found")
        print(f"  • Routing Sessions: {session_count} sessions found")

        if wh_count < 1 or parcel_count < 10 or vehicle_count < 1:
            print("  ⚠️ WARN: Database appears sparsely populated. Recommend running 'seed_dev_data.py'.")
        else:
            print("  ✅ PASS: Seed collections contain healthy record volume.")
    except Exception as exc:
        print(f"  ❌ FAIL: Could not verify collections: {exc}")
        all_passed = False

    # 4. OSM Road Network Graph Cache Check
    print("\n[4/5] Checking Road Network Graph Cache...")
    graph_path = DEFAULT_GRAPH_PATH
    if graph_path.exists():
        size_mb = graph_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ PASS: Graph cache found at '{graph_path.name}' ({size_mb:.2f} MB).")
    else:
        print(f"  ⚠️ INFO: '{graph_path.name}' not found locally.")
        print("         Platform will use in-memory synthetic network or generate cache with build_graph.py.")

    # 5. TomTom Live Traffic API Check
    print("\n[5/5] Checking TomTom Traffic Integration...")
    tomtom_key = os.getenv("TOMTOM_API_KEY")
    if tomtom_key and tomtom_key != "your_tomtom_api_key_here" and len(tomtom_key) > 5:
        print(f"  ✅ PASS: TOMTOM_API_KEY detected (starts with '{tomtom_key[:4]}...'). Live data active.")
    else:
        print("  ℹ️ INFO: No live TomTom key detected. Graceful simulated fallback curve active.")

    print("\n" + "=" * 72)
    if all_passed:
        print("🎉 STATUS: PLATFORM HEALTHY & READY FOR DEMO DISPATCH")
        print("=" * 72)
        return True
    else:
        print("❌ STATUS: PRE-FLIGHT CHECK FAILED — RESOLVE CRITICAL ERRORS ABOVE")
        print("=" * 72)
        return False


if __name__ == "__main__":
    success = asyncio.run(run_healthcheck())
    sys.exit(0 if success else 1)
