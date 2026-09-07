"""
backend/app/qga/decoder.py — Milestone 3.1

Decoder module: converts a grouped-permutation Chromosome into structured,
vehicle-partitioned routes and multi-trip schedules per spec §3d.
"""

from __future__ import annotations

from typing import Any

from app.qga.chromosome import BreakGene, Chromosome, StopGene


def decode_chromosome(
    chromosome: Chromosome,
    stop_metadata: dict[str, dict[str, Any]] | None = None,
    default_warehouse_id: str = "WH-PUNE-001",
    default_vehicle_id: str = "VEH-001",
) -> dict[str, list[dict[str, Any]]]:
    """
    Decode a grouped-permutation chromosome into per-vehicle, per-trip route objects.

    Args:
        chromosome: The Chromosome to decode.
        stop_metadata: Optional dictionary mapping stop_id -> parcel metadata (weight, location, etc.).
        default_warehouse_id: Fallback warehouse ID if no break marker precedes a stop.
        default_vehicle_id: Fallback vehicle ID if no break marker precedes a stop.

    Returns:
        Dictionary mapping vehicle_id -> list of trip dictionaries:
        {
            "VEH-001": [
                {
                    "trip_number": 1,
                    "warehouse_id": "WH-PUNE-001",
                    "stops": ["PAR-PUNE-0001", "PAR-PUNE-0002"],
                    "stop_count": 2,
                    "metadata": [...] (if stop_metadata provided)
                }
            ]
        }
    """
    routes: dict[str, list[dict[str, Any]]] = {}

    current_vehicle = default_vehicle_id
    current_trip_num = 1
    current_warehouse = default_warehouse_id
    current_stops: list[str] = []

    def flush_trip():
        nonlocal current_stops
        if current_vehicle not in routes:
            routes[current_vehicle] = []

        trip_doc: dict[str, Any] = {
            "trip_number": current_trip_num,
            "warehouse_id": current_warehouse,
            "stops": list(current_stops),
            "stop_count": len(current_stops),
        }
        if stop_metadata:
            trip_doc["metadata"] = [
                stop_metadata.get(s, {"stop_id": s}) for s in current_stops
            ]

        routes[current_vehicle].append(trip_doc)
        current_stops = []

    has_active_trip = False

    for gene in chromosome.genes:
        if isinstance(gene, BreakGene):
            if has_active_trip:
                flush_trip()
            current_vehicle = gene.vehicle_id
            current_trip_num = gene.trip_number
            current_warehouse = gene.warehouse_id
            has_active_trip = True
        elif isinstance(gene, StopGene):
            has_active_trip = True
            current_stops.append(gene.stop_id)

    if has_active_trip:
        flush_trip()

    return routes
