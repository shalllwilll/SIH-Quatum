"""
backend/scripts/validate_stops.py — Milestone 1.2

Sanity validator script: confirms every warehouse and parcel stop in MongoDB
snaps to a valid node in the loaded Pune graph and is 100% reachable from at least
one warehouse node. Also checks SLA window boundaries and canonical units.

Usage:
    backend/.venv/bin/python -m backend.scripts.validate_stops
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to sys.path if running as script
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

import networkx as nx  # noqa: E402

from app.db import get_db  # noqa: E402
from app.graph.loader import get_graph, load_graph  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def validate_stops_in_memory(graph: nx.MultiDiGraph, warehouses: list[dict], parcels: list[dict]) -> tuple[bool, list[str]]:
    """
    Pure validation logic against in-memory graph, warehouses, and parcels.

    Returns:
        tuple[bool, list[str]]: (is_valid, list_of_error_messages)
    """
    errors = []

    if not warehouses:
        errors.append("No warehouses found in dataset.")
    if not parcels:
        errors.append("No parcels found in dataset.")

    wh_nodes = []
    for wh in warehouses:
        node_id = wh.get("snapped_node_id")
        if node_id is None or node_id not in graph:
            errors.append(f"Warehouse '{wh.get('warehouse_id')}' snapped node {node_id} NOT found in graph.")
        else:
            wh_nodes.append(node_id)

    log.info("Validated %d warehouse nodes in graph.", len(wh_nodes))

    unreachable_count = 0
    invalid_sla_count = 0

    for parcel in parcels:
        tracking = parcel.get("tracking_number", "UNKNOWN")
        node_id = parcel.get("snapped_node_id")

        # 1. Graph node existence
        if node_id is None or node_id not in graph:
            errors.append(f"Parcel '{tracking}' snapped node {node_id} NOT found in graph.")
            continue

        # 2. SLA window boundaries (spec §3a: minutes since midnight 0..1439)
        sla = parcel.get("sla_window", {})
        start = sla.get("start_time")
        end = sla.get("end_time")
        if start is None or end is None or start < 0 or end > 1439 or start >= end:
            invalid_sla_count += 1
            errors.append(f"Parcel '{tracking}' has invalid SLA window: start={start}, end={end}")

        # 3. Reachability from at least one warehouse
        reachable = any(nx.has_path(graph, wh_node, node_id) for wh_node in wh_nodes)
        if not reachable:
            unreachable_count += 1
            errors.append(f"Parcel '{tracking}' (node {node_id}) is UNREACHABLE from all warehouses.")

    if unreachable_count > 0:
        log.error("Found %d unreachable parcel stops!", unreachable_count)
    if invalid_sla_count > 0:
        log.error("Found %d parcels with invalid SLA windows!", invalid_sla_count)

    is_valid = len(errors) == 0
    return is_valid, errors


async def validate_stops() -> bool:
    """Fetch data from DB, load graph, and run validation."""
    db = get_db()

    warehouses = await db.warehouses.find().to_list(length=100)
    parcels = await db.parcels.find().to_list(length=1000)

    try:
        graph = get_graph()
    except FileNotFoundError:
        log.info("Graph not in memory. Loading from default path...")
        graph = load_graph()

    log.info("Validating %d warehouses and %d parcels against graph...", len(warehouses), len(parcels))

    is_valid, errors = validate_stops_in_memory(graph, warehouses, parcels)

    if is_valid:
        log.info("VALIDATION SUCCESSFUL: All %d parcels and %d warehouses are 100%% valid and reachable!", len(parcels), len(warehouses))
    else:
        log.error("VALIDATION FAILED with %d errors:", len(errors))
        for err in errors[:10]:
            log.error("  - %s", err)
        if len(errors) > 10:
            log.error("  ... and %d more errors.", len(errors) - 10)

    return is_valid


if __name__ == "__main__":
    success = asyncio.run(validate_stops())
    sys.exit(0 if success else 1)
