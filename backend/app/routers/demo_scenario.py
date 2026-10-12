"""
backend/app/routers/demo_scenario.py — Demo Scenario & Disturbance Simulator

Provides dedicated endpoints for SIH demonstrations:
- POST /demo/seed-scenario: Seeds realistic clustered Pune parcels across 3 primary
  warehouse hubs with realistic weights, SLA windows, and vehicle allocations.
- POST /demo/inject-traffic-spike: Injects or clears simulated traffic bottlenecks
  on key Pune arterial corridors (e.g. Pune Station, FC Road, Kharadi) in TomTom cache.
- GET /demo/warehouses: Returns the 3 strategic Pune warehouse distribution hubs.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.db import get_db
from app.traffic import get_traffic_manager
from app.traffic.tomtom_client import FlowSegmentReading

log = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["Demo & Scenario Management"])

# ---------------------------------------------------------------------------
# Strategic Pune Warehouse Definitions
# ---------------------------------------------------------------------------
STRATEGIC_WAREHOUSES = [
    {
        "warehouse_id": "WH-PUNE-001",
        "name": "Central Logistics Hub - Shivajinagar",
        "lat": 18.5308,
        "lon": 73.8475,
        "address": "FP 12, Shivajinagar Commercial Complex, Pune 411005",
        "node_id": 1001,
        "active": True,
        "region": "central",
    },
    {
        "warehouse_id": "WH-PUNE-002",
        "name": "East Logistics Hub - Viman Nagar / Kharadi",
        "lat": 18.5529,
        "lon": 73.9242,
        "address": "Plot 8, EON Tech Corridor, Kharadi-Viman Nagar, Pune 411014",
        "node_id": 1002,
        "active": True,
        "region": "east",
    },
    {
        "warehouse_id": "WH-PUNE-003",
        "name": "West Logistics Hub - Kothrud / Baner",
        "lat": 18.5074,
        "lon": 73.8077,
        "address": "Sector B, Paud Road, Kothrud-Baner Link, Pune 411038",
        "node_id": 1003,
        "active": True,
        "region": "west",
    },
]

# ---------------------------------------------------------------------------
# Authentic Pune Neighborhood Cluster Templates
# ---------------------------------------------------------------------------
PUNE_NEIGHBORHOOD_CLUSTERS = {
    "central": [
        {"name": "FC Road, Deccan Gymkhana", "lat": 18.5196, "lon": 73.8407, "segment_id": "SEG-002"},
        {"name": "JM Road, Shivajinagar", "lat": 18.5314, "lon": 73.8446, "segment_id": "SEG-003"},
        {"name": "Camp MG Road, Pune", "lat": 18.5160, "lon": 73.8765, "segment_id": "SEG-042"},
        {"name": "Pune Railway Station South", "lat": 18.5285, "lon": 73.8745, "segment_id": "SEG-039"},
        {"name": "Swargate Jedhe Chowk", "lat": 18.5015, "lon": 73.8575, "segment_id": "SEG-034"},
        {"name": "Tilak Road, Sadashiv Peth", "lat": 18.5085, "lon": 73.8490, "segment_id": "SEG-035"},
        {"name": "Model Colony, Deep Bungalow", "lat": 18.5350, "lon": 73.8370, "segment_id": "SEG-005"},
        {"name": "Senapati Bapat Road", "lat": 18.5300, "lon": 73.8305, "segment_id": "SEG-006"},
        {"name": "Bund Garden Road", "lat": 18.5360, "lon": 73.8780, "segment_id": "SEG-040"},
        {"name": "Shaniwar Wada Heritage Area", "lat": 18.5195, "lon": 73.8555, "segment_id": "SEG-038"},
    ],
    "east": [
        {"name": "Phoenix Marketcity, Viman Nagar", "lat": 18.5600, "lon": 73.9180, "segment_id": "SEG-057"},
        {"name": "EON Free Zone Phase 1, Kharadi", "lat": 18.5515, "lon": 73.9510, "segment_id": "SEG-059"},
        {"name": "Jogger's Park, Kalyani Nagar", "lat": 18.5482, "lon": 73.9042, "segment_id": "SEG-054"},
        {"name": "Magarpatta Cybercity, Tower 7", "lat": 18.5144, "lon": 73.9304, "segment_id": "SEG-049"},
        {"name": "Kharadi Riverside Road", "lat": 18.5440, "lon": 73.9400, "segment_id": "SEG-060"},
        {"name": "Hadapsar Industrial Estate", "lat": 18.5035, "lon": 73.9312, "segment_id": "SEG-048"},
        {"name": "Wadgaon Sheri Main Road", "lat": 18.5490, "lon": 73.9220, "segment_id": "SEG-058"},
        {"name": "Yerwada Gunjan Chowk", "lat": 18.5525, "lon": 73.8840, "segment_id": "SEG-055"},
        {"name": "Koregaon Park South Main Road", "lat": 18.5320, "lon": 73.8985, "segment_id": "SEG-052"},
        {"name": "Fatima Nagar Junction", "lat": 18.5025, "lon": 73.9010, "segment_id": "SEG-047"},
    ],
    "west": [
        {"name": "Baner High Street Commercial Hub", "lat": 18.5590, "lon": 73.7865, "segment_id": "SEG-009"},
        {"name": "Balewadi Stadium Road", "lat": 18.5720, "lon": 73.7745, "segment_id": "SEG-012"},
        {"name": "Parihar Chowk, Aundh", "lat": 18.5602, "lon": 73.8062, "segment_id": "SEG-007"},
        {"name": "Paud Road, Kothrud", "lat": 18.5110, "lon": 73.8020, "segment_id": "SEG-024"},
        {"name": "Karve Road, Nal Stop", "lat": 18.5070, "lon": 73.8310, "segment_id": "SEG-026"},
        {"name": "Hinjawadi Phase 1 Tech Park", "lat": 18.5913, "lon": 73.7389, "segment_id": "SEG-013"},
        {"name": "Bawdhan Chandani Chowk", "lat": 18.5080, "lon": 73.7825, "segment_id": "SEG-023"},
        {"name": "Pashan Circle, Sus Road", "lat": 18.5375, "lon": 73.7935, "segment_id": "SEG-011"},
        {"name": "Wakad Bridge NH48 Corridor", "lat": 18.5985, "lon": 73.7630, "segment_id": "SEG-014"},
        {"name": "Pimple Saudagar Linear Garden", "lat": 18.5940, "lon": 73.7925, "segment_id": "SEG-015"},
    ],
}

RECIPIENT_NAMES = [
    "Aarav Sharma", "Ananya Joshi", "Rohan Kulkarni", "Priya Deshmukh", "Aditya Patel",
    "Sanya Patil", "Vihaan Rao", "Diya Mehta", "Kabir Bhat", "Isha Verma",
    "Arjun Nair", "Tanvi Agarwal", "Rahul Shinde", "Neha Pawar", "Siddharth Gupta",
    "Pooja Kadam", "Amey Joshi", "Gauri More", "Vikram Rathore", "Kavita Salunkhe",
]

SLA_TIERS = [
    {"label": "Morning Priority", "start": 540, "deadline": 690, "weight_prob": 0.35},     # 09:00 - 11:30
    {"label": "Afternoon Standard", "start": 690, "deadline": 840, "weight_prob": 0.40},   # 11:30 - 14:00
    {"label": "Evening Flexible", "start": 840, "deadline": 1020, "weight_prob": 0.25},    # 14:00 - 17:00
]


# ---------------------------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------------------------
class SeedScenarioRequest(BaseModel):
    num_parcels: int = Field(55, ge=6, le=120, description="Total number of delivery parcels to generate")
    selected_warehouse: str = Field("all", description="Warehouse ID ('WH-PUNE-001', 'WH-PUNE-002', 'WH-PUNE-003', or 'all')")
    vehicle_count: int = Field(11, ge=1, le=15, description="Number of delivery vehicles to allocate")
    vehicle_capacity_kg: float = Field(200.0, ge=50.0, le=500.0, description="Vehicle payload capacity in kilograms")
    seed: int | None = Field(42, description="Random seed for deterministic generation")


class SeedScenarioResponse(BaseModel):
    status: str
    message: str
    parcels_created: int
    warehouses_active: int
    vehicles_active: int
    warehouse_distribution: dict[str, int]
    sample_stops: list[dict[str, Any]]


class TrafficSpikeRequest(BaseModel):
    corridor_key: str = Field("pune_station", description="'pune_station' | 'fc_road' | 'kharadi' | 'baner' | 'reset'")
    active: bool = Field(True, description="True to inject spike, False to clear disturbance")
    severity: float = Field(2.8, ge=1.0, le=4.0, description="Congestion multiplier ratio (1.0 = normal, 2.8 = severe gridlock)")


class TrafficSpikeResponse(BaseModel):
    status: str
    message: str
    corridor_name: str
    segment_id: str
    current_speed_kmh: float
    free_flow_speed_kmh: float
    congestion_ratio: float
    source: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/warehouses", response_model=list[dict[str, Any]])
async def get_demo_warehouses():
    """Retrieve the 3 strategic Pune logistics hubs."""
    return STRATEGIC_WAREHOUSES


@router.post("/seed-scenario", response_model=SeedScenarioResponse, status_code=status.HTTP_200_OK)
async def seed_demo_scenario(req: SeedScenarioRequest):
    """
    Generate realistic clustered Pune delivery parcels snapped across Pune neighborhoods,
    configure vehicle fleet, and update MongoDB collections.
    """
    rng = random.Random(req.seed or 42)
    db = get_db()

    # 1. Ensure Warehouses in DB
    # We update or insert the 3 strategic hubs
    for wh in STRATEGIC_WAREHOUSES:
        await db["warehouses"].update_one(
            {"warehouse_id": wh["warehouse_id"]},
            {"$set": {
                "name": wh["name"],
                "lat": wh["lat"],
                "lon": wh["lon"],
                "address": wh["address"],
                "node_id": wh["node_id"],
                "warehouse_id": wh["warehouse_id"],
                "active": True,
            }},
            upsert=True,
        )

    # 2. Configure Vehicle Fleet
    # Clear existing vehicles and create req.vehicle_count vans
    await db["vehicles"].delete_many({})
    created_vehicles = []
    for i in range(1, req.vehicle_count + 1):
        capacity_parcels = rng.randint(4, 7)
        wh = STRATEGIC_WAREHOUSES[i % 3]
        
        # Strategic starting position, scatter around warehouse
        lat_jitter = rng.uniform(-0.06, 0.06)
        lon_jitter = rng.uniform(-0.06, 0.06)
        
        v_doc = {
            "label": f"Van-{i:02d}",
            "capacity_kg": float(req.vehicle_capacity_kg),
            "capacity_parcels": capacity_parcels,
            "status": "idle",
            "driver_id": f"driver_{i:02d}",
            "current_warehouse_id": wh["warehouse_id"],
            "start_lat": round(wh["lat"] + lat_jitter, 5),
            "start_lon": round(wh["lon"] + lon_jitter, 5),
        }
        res = await db["vehicles"].insert_one(v_doc)
        created_vehicles.append(str(res.inserted_id))

    # 3. Determine Region Distribution for Parcels
    region_targets = []
    if req.selected_warehouse == "WH-PUNE-001":
        region_targets = ["central"] * req.num_parcels
    elif req.selected_warehouse == "WH-PUNE-002":
        region_targets = ["east"] * req.num_parcels
    elif req.selected_warehouse == "WH-PUNE-003":
        region_targets = ["west"] * req.num_parcels
    else:
        # Balanced distribution across all 3 regions
        regions = ["central", "east", "west"]
        for idx in range(req.num_parcels):
            region_targets.append(regions[idx % 3])

    # 4. Generate Parcels with Realistic Pune Neighborhood Jitter
    parcel_docs = []
    warehouse_counts: dict[str, int] = {"WH-PUNE-001": 0, "WH-PUNE-002": 0, "WH-PUNE-003": 0}

    wh_map = {
        "central": "WH-PUNE-001",
        "east": "WH-PUNE-002",
        "west": "WH-PUNE-003",
    }

    sla_tier_choices = [t for t in SLA_TIERS]
    sla_weights = [t["weight_prob"] for t in SLA_TIERS]

    for i in range(1, req.num_parcels + 1):
        region = region_targets[i - 1]
        cluster_stops = PUNE_NEIGHBORHOOD_CLUSTERS[region]
        base_spot = rng.choice(cluster_stops)

        # Realistic street-level jitter (+/- 0.003 to 0.006 deg, ~300-600m within neighborhood)
        lat_jitter = rng.uniform(-0.0045, 0.0045)
        lon_jitter = rng.uniform(-0.0045, 0.0045)
        parcel_lat = round(base_spot["lat"] + lat_jitter, 5)
        parcel_lon = round(base_spot["lon"] + lon_jitter, 5)

        assigned_wh = wh_map[region]
        warehouse_counts[assigned_wh] = warehouse_counts.get(assigned_wh, 0) + 1

        recipient = rng.choice(RECIPIENT_NAMES)
        bldg_num = rng.randint(101, 908)
        address = f"Flat {bldg_num}, {base_spot['name']}, Pune"

        sla_tier = rng.choices(sla_tier_choices, weights=sla_weights, k=1)[0]
        weight_kg = round(rng.uniform(2.5, 17.5), 1)

        priority = rng.choices(["high", "medium", "low"], weights=[0.25, 0.55, 0.20], k=1)[0]

        parcel_docs.append({
            "parcel_id": f"PAR-PUNE-{i:03d}",
            "tracking_number": f"PAR-PUNE-{i:03d}",
            "recipient": recipient,
            "address": address,
            "lat": parcel_lat,
            "lon": parcel_lon,
            "weight_kg": weight_kg,
            "sla_start_min": sla_tier["start"],
            "sla_deadline_min": sla_tier["deadline"],
            "sla_window": (sla_tier["start"], sla_tier["deadline"]),
            "warehouse_id": assigned_wh,
            "priority": priority,
            "status": "pending",
            "dimensions_cm": {
                "length": rng.randint(20, 45),
                "width": rng.randint(15, 35),
                "height": rng.randint(10, 30),
            },
        })

    # Clear previous parcels and insert new realistic clustered parcels
    await db["parcels"].delete_many({})
    if parcel_docs:
        await db["parcels"].insert_many(parcel_docs)

    # 5. Pre-seed realistic day-wise historical sessions for Analysis Dashboard
    import datetime
    await db["routing_sessions"].delete_many({})
    
    now_ts = time.time()
    history_templates = [
        {"day_offset": 5, "day_label": "Day 1 (03 Sep)", "preset": "balanced", "parcels": 44, "dist": 215.4, "sla": 86.4, "fuel": 25.8, "co2": 68.1},
        {"day_offset": 4, "day_label": "Day 2 (04 Sep)", "preset": "min_distance", "parcels": 48, "dist": 198.6, "sla": 89.2, "fuel": 23.8, "co2": 62.8},
        {"day_offset": 3, "day_label": "Day 3 (05 Sep)", "preset": "prioritize_sla", "parcels": 50, "dist": 184.2, "sla": 93.5, "fuel": 22.1, "co2": 58.3},
        {"day_offset": 2, "day_label": "Day 4 (06 Sep)", "preset": "min_fuel", "parcels": 52, "dist": 172.5, "sla": 94.8, "fuel": 19.8, "co2": 52.3},
        {"day_offset": 1, "day_label": "Day 5 (07 Sep)", "preset": "balanced", "parcels": 55, "dist": 165.8, "sla": 96.4, "fuel": 19.2, "co2": 50.7},
        {"day_offset": 0, "day_label": "Today (08 Sep)", "preset": "balanced", "parcels": 55, "dist": 162.5, "sla": 97.2, "fuel": 18.5, "co2": 48.8},
    ]
    historical_sessions = []
    for item in history_templates:
        past_time = now_ts - (item["day_offset"] * 86400)
        dt = datetime.datetime.fromtimestamp(past_time)
        historical_sessions.append({
            "preset": item["preset"],
            "status": "completed",
            "created_at": past_time,
            "cluster_count": 3,
            "vehicle_assignments": [],
            "fitness_history": [],
            "total_distance_km": item["dist"],
            "sla_compliance_pct": item["sla"],
            "seeded": True,
            "assigned": (item["day_offset"] == 0),
            "metadata": {
                "execution_time_ms": 1420.0,
                "parcel_count": item["parcels"],
                "completed_parcels": item["parcels"],
                "fuel_consumed_l": item["fuel"],
                "carbon_emissions_kg": item["co2"],
                "session_label": item["day_label"],
                "day_label": item["day_label"],
                "date_str": dt.strftime("%d/%m/%Y"),
                "date_iso": dt.isoformat(),
            }
        })
    if historical_sessions:
        await db["routing_sessions"].insert_many(historical_sessions)

    log.info(
        "Seeded demo scenario: %d parcels, %d vehicles, %s",
        len(parcel_docs),
        len(created_vehicles),
        warehouse_counts,
    )

    return SeedScenarioResponse(
        status="ok",
        message=f"Demo scenario generated with {len(parcel_docs)} realistic Pune parcels across {len(created_vehicles)} vehicles.",
        parcels_created=len(parcel_docs),
        warehouses_active=len(STRATEGIC_WAREHOUSES),
        vehicles_active=len(created_vehicles),
        warehouse_distribution=warehouse_counts,
        sample_stops=[
            {
                "id": p["parcel_id"],
                "address": p["address"],
                "lat": p["lat"],
                "lon": p["lon"],
                "weight_kg": p["weight_kg"],
                "sla": f"{p['sla_start_min'] // 60:02d}:00 - {p['sla_deadline_min'] // 60:02d}:00",
            }
            for p in parcel_docs[:5]
        ],
    )


# ---------------------------------------------------------------------------
# Traffic Spike Injection Endpoint
# ---------------------------------------------------------------------------
CORRIDOR_SEGMENT_MAP = {
    "pune_station": {"segment_id": "SEG-039", "name": "Pune Station South Gate", "lat": 18.5285, "lon": 73.8745, "free_flow": 38.0},
    "fc_road": {"segment_id": "SEG-002", "name": "FC Road Central", "lat": 18.5236, "lon": 73.8415, "free_flow": 32.0},
    "kharadi": {"segment_id": "SEG-059", "name": "Kharadi Bypass Chowk", "lat": 18.5555, "lon": 73.9390, "free_flow": 45.0},
    "baner": {"segment_id": "SEG-009", "name": "Baner High Street", "lat": 18.5590, "lon": 73.7865, "free_flow": 42.0},
}


@router.post("/inject-traffic-spike", response_model=TrafficSpikeResponse, status_code=status.HTTP_200_OK)
async def inject_traffic_spike(req: TrafficSpikeRequest):
    """
    Inject or reset a simulated traffic surge or road bottleneck on key Pune arterial corridors.
    Directly updates the backend TrafficCache so downstream optimization and live status
    immediately reflect the real-time congestion surge.
    """
    traffic_manager = get_traffic_manager()

    if req.corridor_key == "reset" or not req.active:
        # Reset any simulated disturbance by re-triggering a cycle or restoring normal reading
        for key, corr in CORRIDOR_SEGMENT_MAP.items():
            normal_reading = FlowSegmentReading(
                segment_id=corr["segment_id"],
                lat=corr["lat"],
                lon=corr["lon"],
                current_speed_kmh=corr["free_flow"],
                free_flow_speed_kmh=corr["free_flow"],
                congestion_ratio=1.0,
                confidence=1.0,
                source="live",
            )
            traffic_manager.cache.update_reading(normal_reading)

        return TrafficSpikeResponse(
            status="ok",
            message="All simulated road disturbances cleared. Traffic restored to live telemetry baseline.",
            corridor_name="All Corridors",
            segment_id="ALL",
            current_speed_kmh=38.0,
            free_flow_speed_kmh=38.0,
            congestion_ratio=1.0,
            source="live",
        )

    corridor = CORRIDOR_SEGMENT_MAP.get(req.corridor_key, CORRIDOR_SEGMENT_MAP["pune_station"])
    free_flow = corridor["free_flow"]
    congested_speed = round(max(5.0, free_flow / req.severity), 1)

    reading = FlowSegmentReading(
        segment_id=corridor["segment_id"],
        lat=corridor["lat"],
        lon=corridor["lon"],
        current_speed_kmh=congested_speed,
        free_flow_speed_kmh=free_flow,
        congestion_ratio=round(req.severity, 2),
        confidence=1.0,
        source="simulated_disturbance",
    )

    traffic_manager.cache.update_reading(reading)
    log.info(
        "Injected traffic bottleneck at %s (%s): speed %s km/h, ratio %sx",
        corridor["name"],
        corridor["segment_id"],
        congested_speed,
        req.severity,
    )

    return TrafficSpikeResponse(
        status="ok",
        message=f"Simulated traffic blockage injected at {corridor['name']}! Congestion ratio surged to {req.severity}x.",
        corridor_name=corridor["name"],
        segment_id=corridor["segment_id"],
        current_speed_kmh=congested_speed,
        free_flow_speed_kmh=free_flow,
        congestion_ratio=round(req.severity, 2),
        source="simulated_disturbance",
    )
