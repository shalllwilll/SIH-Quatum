"""
scripts/seed_realistic_history.py
Seeds realistic 6-day fleet history for the Analysis Dashboard.
"""

import asyncio
import datetime
import os
import time
from dotenv import load_dotenv

load_dotenv("backend/.env")
from app.db import get_db

async def seed_history():
    db = get_db()
    
    # 1. Clean up old routing sessions
    deleted = await db["routing_sessions"].delete_many({})
    print(f"Cleaned up {deleted.deleted_count} old routing sessions.")

    # 2. Base timestamp for today: 2026-09-08 09:00:00 local time
    # 1788813000 is approx Sep 8 2026 early morning
    now_ts = time.time()
    
    # Realistic 6-day progression showing fleet optimization ROI
    history_templates = [
        {
            "day_offset": 5,
            "day_label": "Day 1 (03 Sep)",
            "preset": "balanced",
            "parcels": 44,
            "distance_km": 215.4,
            "sla_pct": 86.4,
            "fuel_l": 25.8,
            "co2_kg": 68.1,
            "status": "completed",
            "notes": "Baseline unoptimized heuristic routing with multiple cross-town overlapping detours."
        },
        {
            "day_offset": 4,
            "day_label": "Day 2 (04 Sep)",
            "preset": "min_distance",
            "parcels": 48,
            "distance_km": 198.6,
            "sla_pct": 89.2,
            "fuel_l": 23.8,
            "co2_kg": 62.8,
            "status": "completed",
            "notes": "Initial spatial clustering reduced detour distance by 7.8%."
        },
        {
            "day_offset": 3,
            "day_label": "Day 3 (05 Sep)",
            "preset": "prioritize_sla",
            "parcels": 50,
            "distance_km": 184.2,
            "sla_pct": 93.5,
            "fuel_l": 22.1,
            "co2_kg": 58.3,
            "status": "completed",
            "notes": "Leiden community detection introduced; SLA compliance increased to 93.5%."
        },
        {
            "day_offset": 2,
            "day_label": "Day 4 (06 Sep)",
            "preset": "min_fuel",
            "parcels": 52,
            "distance_km": 172.5,
            "sla_pct": 94.8,
            "fuel_l": 19.8,
            "co2_kg": 52.3,
            "status": "completed",
            "notes": "Eco-routing speed-profile curves reduced fleet diesel consumption to under 20L."
        },
        {
            "day_offset": 1,
            "day_label": "Day 5 (07 Sep)",
            "preset": "balanced",
            "parcels": 55,
            "distance_km": 165.8,
            "sla_pct": 96.4,
            "fuel_l": 19.2,
            "co2_kg": 50.7,
            "status": "completed",
            "notes": "Full QGA + QPSO quantum hybrid routing across 3 Pune strategic depots."
        },
        {
            "day_offset": 0,
            "day_label": "Today (08 Sep)",
            "preset": "balanced",
            "parcels": 55,
            "distance_km": 162.5,
            "sla_pct": 97.2,
            "fuel_l": 18.5,
            "co2_kg": 48.8,
            "status": "completed",
            "notes": "Current production dispatch: 24.5% cumulative mileage reduction and 97.2% on-time rate."
        }
    ]

    docs_to_insert = []
    for item in history_templates:
        session_ts = now_ts - (item["day_offset"] * 86400)
        dt = datetime.datetime.fromtimestamp(session_ts)
        
        doc = {
            "preset": item["preset"],
            "status": item["status"],
            "created_at": session_ts,
            "cluster_count": 3,
            "vehicle_assignments": [],
            "fitness_history": [],
            "total_distance_km": item["distance_km"],
            "sla_compliance_pct": item["sla_pct"],
            "seeded": True,
            "assigned": (item["day_offset"] == 0),
            "metadata": {
                "execution_time_ms": 1420.0 + (5 - item["day_offset"]) * 120,
                "parcel_count": item["parcels"],
                "completed_parcels": item["parcels"],
                "fuel_consumed_l": item["fuel_l"],
                "carbon_emissions_kg": item["co2_kg"],
                "session_label": item["day_label"],
                "day_label": item["day_label"],
                "date_str": dt.strftime("%d/%m/%Y"),
                "date_iso": dt.isoformat(),
                "notes": item["notes"]
            }
        }
        docs_to_insert.append(doc)

    await db["routing_sessions"].insert_many(docs_to_insert)
    print(f"Successfully inserted {len(docs_to_insert)} day-wise realistic routing sessions!")

    # 3. Synchronize delivery_events count to match realistic deliveries
    await db["delivery_events"].delete_many({})
    events = []
    
    # We fetch the inserted sessions to link real session IDs
    saved_sessions = await db["routing_sessions"].find().sort("created_at", 1).to_list(10)
    
    for s_idx, session_doc in enumerate(saved_sessions):
        s_id = str(session_doc["_id"])
        item = history_templates[s_idx]
        s_ts = float(session_doc["created_at"])
        n_parcels = item["parcels"]
        late_count = int(round(n_parcels * (1.0 - item["sla_pct"] / 100.0)))
        
        for p_idx in range(n_parcels):
            is_late = (p_idx < late_count)
            # recorded_at_min: e.g. 540 (09:00 AM) + minutes offset
            minute_of_day = 540 + int((p_idx / max(1, n_parcels)) * 360) # within 6-hour dispatch window
            events.append({
                "routing_session_id": s_id,
                "vehicle_id": f"Van-{(p_idx % 11) + 1}",
                "parcel_id": f"PAR-HIST-{s_idx+1:02d}-{p_idx+1:03d}",
                "status": "delivered",
                "recorded_at_min": int(minute_of_day),
                "recorded_at_wall": float(s_ts + (minute_of_day * 60)),
                "is_late": bool(is_late),
                "note": "Late delivery - traffic delay" if is_late else "Delivered on schedule"
            })
            
    await db["delivery_events"].insert_many(events)
    print(f"Synchronized {len(events)} delivery events matching exact historical SLA compliance.")

if __name__ == "__main__":
    asyncio.run(seed_history())
