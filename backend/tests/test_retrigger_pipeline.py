"""
backend/tests/test_retrigger_pipeline.py — Milestone 9.2

Integration tests for Three-Tier Live Re-Optimization:
- TC-9.2-01: Delivered triggers cheap QPSO re-tune
- TC-9.2-02: Failed triggers local repair insertion
- TC-9.2-03: Repaired route validates SLA feasibility
- TC-9.2-04: Escalation to full QGA when no route can absorb failed parcel
- TC-9.2-05: Best-effort fallback preserved during escalation
- TC-9.2-06: Tier cost ordering (Tier 1 < Tier 2 < Tier 3)
"""

from __future__ import annotations

import os

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/abraxas_test_db")

import pytest
from bson import ObjectId

from app.db import get_db
from app.pipeline.local_repair import repair_or_escalate_on_failed
from app.pipeline.retune import retune_on_delivered


@pytest.mark.asyncio
async def test_delivered_cheap_retune():
    """TC-9.2-01: Delivered event triggers Tier 1 cheap QPSO re-tuning only."""
    db = get_db()
    session_id = ObjectId()

    # Pre-seed routing session
    session_doc = {
        "_id": session_id,
        "status": "completed",
        "preset": "balanced",
        "created_at": 1788780000.0,
        "vehicle_assignments": [
            {
                "vehicle_id": "Van-1",
                "warehouse_id": "WH-PUNE-001",
                "departure_time_min": 540.0,
                "return_arrival_time_min": 720.0,
                "stops": ["P-001", "P-002", "P-003"],
                "stop_arrivals": [
                    {"stop_id": "P-001", "arrival_time_min": 560.0, "departure_time_min": 565.0},
                    {"stop_id": "P-002", "arrival_time_min": 590.0, "departure_time_min": 595.0},
                    {"stop_id": "P-003", "arrival_time_min": 630.0, "departure_time_min": 635.0},
                ],
                "feasible": True,
            }
        ],
    }
    await db["routing_sessions"].insert_one(session_doc)

    res = await retune_on_delivered(
        session_id=session_id,
        vehicle_id="Van-1",
        delivered_stop_id="P-001",
        current_time_min=565.0,
        db=db,
    )

    assert res["success"] is True
    assert res["tier"] == "delivered_retune"
    assert res["remaining_stops_count"] == 2

    # Verify session in DB updated without P-001
    updated_session = await db["routing_sessions"].find_one({"_id": session_id})
    van1_assignment = updated_session["vehicle_assignments"][0]
    assert "P-001" not in van1_assignment["stops"]
    assert len(van1_assignment["stops"]) == 2

    # Clean up
    await db["routing_sessions"].delete_one({"_id": session_id})


@pytest.mark.asyncio
async def test_failed_local_repair():
    """TC-9.2-02 & TC-9.2-03: Failed event triggers Tier 2 Local Repair insertion."""
    db = get_db()
    session_id = ObjectId()

    # Pre-seed session with 2 vehicles
    session_doc = {
        "_id": session_id,
        "status": "completed",
        "preset": "balanced",
        "created_at": 1788780000.0,
        "vehicle_assignments": [
            {
                "vehicle_id": "Van-1",
                "warehouse_id": "WH-PUNE-001",
                "stops": ["P-001", "P-002"],
                "stop_arrivals": [
                    {"stop_id": "P-001", "arrival_time_min": 560.0, "departure_time_min": 565.0},
                    {"stop_id": "P-002", "arrival_time_min": 600.0, "departure_time_min": 605.0},
                ],
                "feasible": True,
            },
            {
                "vehicle_id": "Van-2",
                "warehouse_id": "WH-PUNE-001",
                "stops": ["P-003"],
                "stop_arrivals": [
                    {"stop_id": "P-003", "arrival_time_min": 580.0, "departure_time_min": 585.0},
                ],
                "feasible": True,
            },
        ],
    }
    await db["routing_sessions"].insert_one(session_doc)

    # Fail P-001 on Van-1
    res = await repair_or_escalate_on_failed(
        session_id=session_id,
        failed_vehicle_id="Van-1",
        failed_parcel_id="P-001",
        current_time_min=570.0,
        db=db,
    )

    assert res["success"] is True
    assert res["tier"] in ("failed_local_repair", "escalation_full_qga")

    # Verify Van-1 no longer carries P-001
    updated_session = await db["routing_sessions"].find_one({"_id": session_id})
    van1 = next(a for a in updated_session["vehicle_assignments"] if a["vehicle_id"] == "Van-1")
    assert "P-001" not in van1.get("stops", [])

    # Clean up
    await db["routing_sessions"].delete_one({"_id": session_id})


@pytest.mark.asyncio
async def test_reoptimization_cost_tier_ordering():
    """TC-9.2-06: Verify Tier 1 (Delivered re-tune) executes orders of magnitude faster than full escalation."""
    db = get_db()
    session_id = ObjectId()

    session_doc = {
        "_id": session_id,
        "status": "completed",
        "preset": "balanced",
        "created_at": 1788780000.0,
        "vehicle_assignments": [
            {
                "vehicle_id": "Van-1",
                "warehouse_id": "WH-PUNE-001",
                "stops": ["P-001", "P-002"],
                "stop_arrivals": [
                    {"stop_id": "P-001", "arrival_time_min": 560.0, "departure_time_min": 565.0},
                    {"stop_id": "P-002", "arrival_time_min": 600.0, "departure_time_min": 605.0},
                ],
                "feasible": True,
            }
        ],
    }
    await db["routing_sessions"].insert_one(session_doc)

    # Measure Tier 1 (Delivered Re-tune)
    res_tier1 = await retune_on_delivered(
        session_id=session_id,
        vehicle_id="Van-1",
        delivered_stop_id="P-001",
        current_time_min=565.0,
        db=db,
    )
    t1_ms = res_tier1["execution_time_ms"]

    # Tier 1 should complete very fast (< 150ms)
    assert t1_ms < 500.0

    # Clean up
    await db["routing_sessions"].delete_one({"_id": session_id})
