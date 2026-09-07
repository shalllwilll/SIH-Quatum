"""
backend/scripts/seed_historical_sessions.py — Milestone 10.1

Seeds 4 historical routing sessions with linked delivery events in MongoDB:
- Generates a deliberate improving trend in SLA compliance and fuel efficiency over 4 days.
- Each historical session is marked with `seeded: True`.
- Populates realistic delivery events with mixed outcomes (DELIVERED, FAILED) for analytics aggregations.
- Idempotent: cleanly replaces existing seeded sessions without polluting live demo data.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any

from bson import ObjectId

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/logistics_db")

from app.db import get_client, get_db

# 4-Day Historical Trend Dataset (improving SLA compliance & fuel efficiency)
HISTORICAL_SESSIONS: list[dict[str, Any]] = [
    {
        "days_ago": 4,
        "preset": "balanced",
        "total_distance_km": 148.5,
        "sla_compliance_pct": 74.2,
        "fuel_efficiency_score": 65.0,  # lower is worse
        "vehicles": [
            {"id": "Van-1", "stops_count": 6, "delivered": 4, "failed": 2, "late": 1, "distance_km": 52.0},
            {"id": "Van-2", "stops_count": 5, "delivered": 4, "failed": 1, "late": 1, "distance_km": 48.5},
            {"id": "Van-3", "stops_count": 6, "delivered": 5, "failed": 1, "late": 2, "distance_km": 48.0},
        ],
        "violations": [
            {"type": "SLA_WINDOW_MISS", "count": 4, "details": "Delayed in Pune Station traffic corridor"},
            {"type": "CAPACITY_OVERRUN", "count": 1, "details": "Van-1 exceeded rated capacity by 15kg before re-balance"},
        ],
    },
    {
        "days_ago": 3,
        "preset": "min_distance",
        "total_distance_km": 132.0,
        "sla_compliance_pct": 81.5,
        "fuel_efficiency_score": 73.5,
        "vehicles": [
            {"id": "Van-1", "stops_count": 6, "delivered": 5, "failed": 1, "late": 1, "distance_km": 46.0},
            {"id": "Van-2", "stops_count": 6, "delivered": 5, "failed": 1, "late": 0, "distance_km": 43.0},
            {"id": "Van-3", "stops_count": 5, "delivered": 5, "failed": 0, "late": 1, "distance_km": 43.0},
        ],
        "violations": [
            {"type": "SLA_WINDOW_MISS", "count": 2, "details": "Evening congestion on Senapati Bapat Rd"},
        ],
    },
    {
        "days_ago": 2,
        "preset": "min_fuel",
        "total_distance_km": 124.8,
        "sla_compliance_pct": 88.0,
        "fuel_efficiency_score": 84.0,
        "vehicles": [
            {"id": "Van-1", "stops_count": 6, "delivered": 6, "failed": 0, "late": 1, "distance_km": 42.0},
            {"id": "Van-2", "stops_count": 6, "delivered": 5, "failed": 1, "late": 0, "distance_km": 41.5},
            {"id": "Van-3", "stops_count": 6, "delivered": 6, "failed": 0, "late": 0, "distance_km": 41.3},
        ],
        "violations": [
            {"type": "SLA_WINDOW_MISS", "count": 1, "details": "Customer address gated access delay"},
        ],
    },
    {
        "days_ago": 1,
        "preset": "prioritize_sla",
        "total_distance_km": 116.4,
        "sla_compliance_pct": 95.8,
        "fuel_efficiency_score": 92.5,
        "vehicles": [
            {"id": "Van-1", "stops_count": 7, "delivered": 7, "failed": 0, "late": 0, "distance_km": 39.2},
            {"id": "Van-2", "stops_count": 6, "delivered": 6, "failed": 0, "late": 0, "distance_km": 38.6},
            {"id": "Van-3", "stops_count": 6, "delivered": 6, "failed": 0, "late": 1, "distance_km": 38.6},
        ],
        "violations": [],
    },
]


async def seed_historical_sessions() -> int:
    """Seed historical sessions and delivery events into MongoDB."""
    db = get_db()
    current_wall_time = time.time()
    day_sec = 86400

    print("Cleaning up existing seeded historical sessions...")
    # Delete prior seeded sessions and events to maintain idempotency
    del_sessions = await db["routing_sessions"].delete_many({"seeded": True})
    del_events = await db["delivery_events"].delete_many({"seeded": True})
    print(f"Removed {del_sessions.deleted_count} old sessions and {del_events.deleted_count} old events.")

    sessions_created = 0
    events_created = 0

    for s_idx, data in enumerate(HISTORICAL_SESSIONS):
        s_id = ObjectId()
        session_timestamp = current_wall_time - (data["days_ago"] * day_sec)

        vehicle_assignments = []
        all_session_events = []

        for v_info in data["vehicles"]:
            v_id = v_info["id"]
            stops_count = v_info["stops_count"]
            stops = [f"HIST-{data['days_ago']}D-{v_id}-{i:02d}" for i in range(1, stops_count + 1)]

            stop_arrivals = []
            start_min = 540 + s_idx * 5  # 09:00 AM
            for i, st_id in enumerate(stops):
                arr = start_min + i * 25
                dep = arr + 5
                stop_arrivals.append({
                    "stop_id": st_id,
                    "arrival_time_min": arr,
                    "departure_time_min": dep,
                })

                # Create delivery event
                is_failed = (i < v_info["failed"])
                is_late = (i >= v_info["failed"] and i < v_info["failed"] + v_info.get("late", 0))

                evt_status = "failed" if is_failed else "delivered"
                evt_doc = {
                    "routing_session_id": str(s_id),
                    "vehicle_id": v_id,
                    "parcel_id": st_id,
                    "status": evt_status,
                    "recorded_at_min": dep,
                    "recorded_at_wall": session_timestamp + (dep * 60),
                    "note": "Late arrival due to traffic" if is_late else ("Premises closed" if is_failed else "On-time drop"),
                    "seeded": True,
                    "is_late": is_late,
                    "days_ago": data["days_ago"],
                }
                all_session_events.append(evt_doc)

            vehicle_assignments.append({
                "vehicle_id": v_id,
                "cluster_id": s_idx + 1,
                "warehouse_id": "WH-PUNE-001",
                "departure_time_min": start_min,
                "return_arrival_time_min": start_min + stops_count * 25 + 20,
                "total_duration_min": stops_count * 25 + 20,
                "distance_km": v_info["distance_km"],
                "stops": stops,
                "stop_arrivals": stop_arrivals,
                "feasible": v_info["failed"] == 0,
            })

        session_doc = {
            "_id": s_id,
            "preset": data["preset"],
            "status": "completed",
            "created_at": session_timestamp,
            "total_distance_km": data["total_distance_km"],
            "sla_compliance_pct": data["sla_compliance_pct"],
            "cluster_count": len(data["vehicles"]),
            "vehicle_assignments": vehicle_assignments,
            "seeded": True,
            "metadata": {
                "fuel_efficiency_score": data["fuel_efficiency_score"],
                "violations": data["violations"],
                "execution_time_ms": 1250.0 + (4 - data["days_ago"]) * 180.0,
                "feasible": True,
                "fallback_applied": False,
            },
        }

        await db["routing_sessions"].insert_one(session_doc)
        sessions_created += 1

        if all_session_events:
            await db["delivery_events"].insert_many(all_session_events)
            events_created += len(all_session_events)

    print(f"✅ Successfully seeded {sessions_created} historical sessions and {events_created} linked delivery events!")
    return sessions_created


if __name__ == "__main__":
    asyncio.run(seed_historical_sessions())
