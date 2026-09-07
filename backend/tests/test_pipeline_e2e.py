"""
backend/tests/test_pipeline_e2e.py — Milestone 4.3 Test Suite

Test Cases:
  TC-4.3-01: Feasible-from-start route finishes without bounce-back (bounceback_count == 0)
  TC-4.3-02: Infeasible timing triggers targeted QGA bounce-back re-optimization
  TC-4.3-03: Bounce-back retry successfully resolves timing conflict
  TC-4.3-04: Structurally impossible SLA triggers best-effort fallback without dropping parcels
  TC-4.3-05: Retry cap is strictly enforced (attempts <= max_bounceback_retries)
  TC-4.3-06: Full routing session document is persisted with complete schema & canonical units
"""

import pytest

from app.db import get_db
from app.models.routing_session import SessionStatus
from app.pipeline.orchestrator import PipelineResult, run_hybrid_routing_pipeline


def _make_sample_parcels(count: int = 10, default_sla: tuple[int, int] = (540, 1020)) -> list[dict]:
    """Helper to create sample parcels with geographic coordinates in Pune."""
    parcels = []
    for i in range(1, count + 1):
        parcels.append({
            "tracking_number": f"PAR-PUNE-{i:04d}",
            "location": {"type": "Point", "coordinates": [73.85 + (i * 0.005), 18.52 + (i * 0.005)]},
            "weight_kg": 5.0,
            "sla_window": {"start_time": default_sla[0], "end_time": default_sla[1]},
            "priority": "medium",
            "status": "pending",
        })
    return parcels


@pytest.mark.asyncio
async def test_tc_4_3_01_feasible_no_bounceback():
    """TC-4.3-01: Generous SLA windows complete with 0 bounce-back retries."""
    parcels = _make_sample_parcels(count=6, default_sla=(480, 1200))

    result = await run_hybrid_routing_pipeline(
        parcels=parcels,
        vehicles=["VEH-001", "VEH-002"],
        preset="balanced",
        max_bounceback_retries=3,
        persist_to_db=False,
        seed=42,
    )

    assert isinstance(result, PipelineResult)
    assert result.feasible is True
    assert result.fallback_applied is False
    assert result.bounceback_count == 0
    assert result.status == SessionStatus.COMPLETED
    assert result.sla_compliance_pct == 100.0


@pytest.mark.asyncio
async def test_tc_4_3_02_and_05_retry_cap_enforced():
    """TC-4.3-02 & TC-4.3-05: Infeasible route triggers bounce-back and respects retry cap."""
    # Impossible SLA window: parcel delivery required at minute 100 (well before warehouse opens at 360)
    parcels = _make_sample_parcels(count=4, default_sla=(50, 100))

    result = await run_hybrid_routing_pipeline(
        parcels=parcels,
        vehicles=["VEH-001"],
        preset="prioritize_sla",
        max_bounceback_retries=3,
        persist_to_db=False,
        seed=42,
    )

    # Bounce-back was triggered
    assert result.bounceback_count > 0
    assert result.bounceback_count <= 3
    # Cap reached -> fallback applied
    assert result.fallback_applied is True
    assert result.feasible is False


@pytest.mark.asyncio
async def test_tc_4_3_04_best_effort_fallback_preserves_all_parcels():
    """TC-4.3-04: Best-effort fallback ensures all parcels remain assigned (never dropped)."""
    parcels = _make_sample_parcels(count=8, default_sla=(10, 20))  # Impossible SLA

    result = await run_hybrid_routing_pipeline(
        parcels=parcels,
        vehicles=["VEH-001", "VEH-002"],
        max_bounceback_retries=2,
        persist_to_db=False,
        seed=42,
    )

    assert result.fallback_applied is True

    # Count all routed parcels across vehicle assignments
    all_assigned_stops = []
    for v_plan in result.vehicle_assignments:
        all_assigned_stops.extend(v_plan["stops"])

    # All 8 parcels must be present
    assert len(all_assigned_stops) == 8
    expected_ids = {p["tracking_number"] for p in parcels}
    assert set(all_assigned_stops) == expected_ids


@pytest.mark.asyncio
async def test_tc_4_3_06_session_persistence_and_schema():
    """TC-4.3-06 (Integration): Persists full session into MongoDB with canonical units."""
    db = get_db()
    parcels = _make_sample_parcels(count=5, default_sla=(480, 1100))

    result = await run_hybrid_routing_pipeline(
        parcels=parcels,
        vehicles=["VEH-001", "VEH-002"],
        preset="balanced",
        persist_to_db=True,
        db=db,
        seed=42,
    )

    assert result.session_id is not None

    # Query back from MongoDB
    from bson import ObjectId
    doc = await db.routing_sessions.find_one({"_id": ObjectId(result.session_id)})
    assert doc is not None

    assert doc["status"] == "completed"
    assert doc["preset"] == "balanced"
    assert "vehicle_assignments" in doc
    assert "fitness_history" in doc
    assert doc["total_distance_km"] > 0.0
    assert 0.0 <= doc["sla_compliance_pct"] <= 100.0

    # Cleanup test session
    await db.routing_sessions.delete_one({"_id": ObjectId(result.session_id)})
