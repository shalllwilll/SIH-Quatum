"""
backend/scripts/generate_stops.py — Milestone 1.2

Generates realistic problem instance (4 warehouses + 110 delivery stops) snapped
to the largest strongly connected component (SCC) of the Pune road network graph,
ensuring 100% graph reachability and deterministic repeatability.

Usage:
    backend/.venv/bin/python -m backend.scripts.generate_stops
"""

from __future__ import annotations

import asyncio
import logging
import random
import sys
from pathlib import Path

# Add backend directory to sys.path if running as script
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.db import get_db  # noqa: E402
from app.graph.loader import get_graph, load_graph  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Warehouse Definitions (Pune Urban Region)
# ---------------------------------------------------------------------------
WAREHOUSES = [
    {
        "warehouse_id": "WH-PUNE-001",
        "name": "Central Logistics Hub - Shivajinagar",
        "lon": 73.8475,
        "lat": 18.5308,
        "operating_hours": {"start_time": 360, "end_time": 1320},  # 06:00 - 22:00
        "active": True,
    },
    {
        "warehouse_id": "WH-PUNE-002",
        "name": "East Logistics Hub - Hadapsar",
        "lon": 73.9260,
        "lat": 18.5089,
        "operating_hours": {"start_time": 360, "end_time": 1320},
        "active": True,
    },
    {
        "warehouse_id": "WH-PUNE-003",
        "name": "West Logistics Hub - Kothrud",
        "lon": 73.8077,
        "lat": 18.5074,
        "operating_hours": {"start_time": 360, "end_time": 1320},
        "active": True,
    },
    {
        "warehouse_id": "WH-PUNE-004",
        "name": "North Logistics Hub - Pimpri-Chinchwad",
        "lon": 73.7997,
        "lat": 18.6298,
        "operating_hours": {"start_time": 360, "end_time": 1320},
        "active": True,
    },
]

# Realistic Pune Localities & Recipients
PUNE_LOCALITIES = [
    "Viman Nagar", "Koregaon Park", "Baner", "Wakad", "Aundh", "Deccan Gymkhana",
    "Swargate", "Pune Camp", "Kondhwa", "Wagholi", "Kothrud", "Hadapsar",
    "Pimple Saudagar", "Bawdhan", "Katraj", "Magarpatta", "Kharadi", "Pashan",
]
RECIPIENTS = [
    "Aarav Sharma", "Ananya Joshi", "Rohan Kulkarni", "Priya Deshmukh", "Aditya Patel",
    "Sanya Patil", "Vihaan Rao", "Diya Mehta", "Kabir Bhat", "Isha Verma",
    "Arjun Nair", "Tanvi Agarwal", "Rahul Shinde", "Neha Pawar", "Siddharth Gupta",
]

SLA_SLOTS = [
    (540, 660),    # 09:00 - 11:00
    (660, 780),    # 11:00 - 13:00
    (780, 900),    # 13:00 - 15:00
    (900, 1020),   # 15:00 - 17:00
    (1020, 1140),  # 17:00 - 19:00
]


def generate_seed_data(seed: int = 42, num_parcels: int = 110):
    """
    Generate warehouses and parcels snapped to the Pune graph.

    Args:
        seed: Random seed for deterministic generation.
        num_parcels: Number of parcels to generate (default: 110).

    Returns:
        tuple[list[dict], list[dict]]: (warehouse_docs, parcel_docs)
    """
    import networkx as nx
    import osmnx as ox

    rng = random.Random(seed)

    # 1. Load graph
    try:
        graph = get_graph()
    except FileNotFoundError:
        log.info("Graph not loaded in memory. Attempting to load from default path...")
        graph = load_graph()

    if "crs" not in graph.graph:
        graph.graph["crs"] = "epsg:4326"

    # 2. Extract largest strongly connected component (SCC) for 100% reachability
    sccs = list(nx.strongly_connected_components(graph))
    largest_scc_nodes = max(sccs, key=len)
    log.info(
        "Loaded graph with %d nodes. Largest SCC has %d nodes.",
        graph.number_of_nodes(),
        len(largest_scc_nodes),
    )

    scc_graph = graph.subgraph(largest_scc_nodes)

    # 3. Snap warehouses to nearest nodes in the largest SCC
    warehouse_docs = []
    wh_node_ids = []
    for wh in WAREHOUSES:
        # Nearest node in graph
        nearest_node = ox.distance.nearest_nodes(
            scc_graph, X=wh["lon"], Y=wh["lat"]
        )
        doc = {
            "warehouse_id": wh["warehouse_id"],
            "name": wh["name"],
            "location": {
                "type": "Point",
                "coordinates": [wh["lon"], wh["lat"]],
            },
            "snapped_node_id": int(nearest_node),
            "operating_hours": wh["operating_hours"],
            "active": wh["active"],
        }
        warehouse_docs.append(doc)
        wh_node_ids.append(int(nearest_node))
        log.info(
            "Snapped Warehouse %s (%s) -> Graph Node %d",
            wh["warehouse_id"],
            wh["name"],
            nearest_node,
        )

    # 4. Sample nodes from largest SCC for delivery stops (allows multiple parcels per node block)
    sampled_nodes = rng.choices(sorted(largest_scc_nodes), k=num_parcels)

    parcel_docs = []
    for i, node_id in enumerate(sampled_nodes, start=1):
        node_data = graph.nodes[node_id]
        lon = float(node_data.get("x", 73.8567))
        lat = float(node_data.get("y", 18.5204))

        locality = rng.choice(PUNE_LOCALITIES)
        recipient = rng.choice(RECIPIENTS)
        sla_start, sla_end = rng.choice(SLA_SLOTS)
        assigned_wh = rng.choice(warehouse_docs)["warehouse_id"]
        priority = rng.choices(
            ["low", "medium", "high"], weights=[0.2, 0.6, 0.2]
        )[0]

        parcel_doc = {
            "tracking_number": f"PAR-PUNE-{i:04d}",
            "recipient": recipient,
            "address": f"Building {rng.randint(1, 99)}, {locality}, Pune",
            "location": {
                "type": "Point",
                "coordinates": [lon, lat],
            },
            "snapped_node_id": int(node_id),
            "warehouse_id": assigned_wh,
            "weight_kg": round(rng.uniform(1.0, 15.0), 1),
            "dimensions_cm": {
                "length": rng.randint(15, 40),
                "width": rng.randint(10, 30),
                "height": rng.randint(5, 25),
            },
            "sla_window": {
                "start_time": sla_start,
                "end_time": sla_end,
            },
            "priority": priority,
            "status": "pending",
        }
        parcel_docs.append(parcel_doc)

    return warehouse_docs, parcel_docs


async def seed_stops(seed: int = 42, num_parcels: int = 110):
    """Insert generated warehouses and parcels into MongoDB."""
    db = get_db()

    warehouse_docs, parcel_docs = generate_seed_data(seed=seed, num_parcels=num_parcels)

    # Drop existing collections to replace with real graph instance
    await db.warehouses.drop()
    await db.parcels.drop()

    if warehouse_docs:
        res_wh = await db.warehouses.insert_many(warehouse_docs)
        log.info("Inserted %d warehouse documents.", len(res_wh.inserted_ids))

    if parcel_docs:
        res_p = await db.parcels.insert_many(parcel_docs)
        log.info("Inserted %d parcel documents.", len(res_p.inserted_ids))

    log.info("Seeding complete: %d warehouses, %d parcels.", len(warehouse_docs), len(parcel_docs))


if __name__ == "__main__":
    asyncio.run(seed_stops())
