"""
backend/app/qga/chromosome.py — Milestone 3.1

Grouped-permutation chromosome encoding for QGA per spec §3d.
Encodes a permutation of delivery stops partitioned by break markers
into per-vehicle, per-trip sub-routes with dynamic warehouse assignment.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum
from typing import NamedTuple


class GeneType(StrEnum):
    STOP = "stop"
    BREAK = "break"


class StopGene(NamedTuple):
    stop_id: str
    warehouse_id: str | None = None

    @property
    def is_break(self) -> bool:
        return False


class BreakGene(NamedTuple):
    vehicle_id: str
    trip_number: int = 1
    warehouse_id: str = "WH-PUNE-001"

    @property
    def is_break(self) -> bool:
        return True


Gene = StopGene | BreakGene


@dataclass
class Chromosome:
    """Grouped-permutation chromosome consisting of stop genes and break genes."""
    genes: list[Gene]

    def stops(self) -> list[str]:
        """Extract ordered stop IDs from chromosome."""
        return [g.stop_id for g in self.genes if isinstance(g, StopGene)]

    def breaks(self) -> list[BreakGene]:
        """Extract break markers from chromosome."""
        return [g for g in self.genes if isinstance(g, BreakGene)]

    def copy(self) -> Chromosome:
        """Return a shallow copy of the chromosome genes list."""
        return Chromosome(genes=list(self.genes))

    def __len__(self) -> int:
        return len(self.genes)

    def __getitem__(self, index: int) -> Gene:
        return self.genes[index]

    def __iter__(self):
        return iter(self.genes)


def generate_random_chromosome(
    stops: list[str],
    vehicles: list[str],
    warehouse_id: str = "WH-PUNE-001",
    trips_per_vehicle: int = 1,
    seed: int | None = None,
) -> Chromosome:
    """
    Generate a random valid chromosome within a single Leiden cluster.

    Args:
        stops: List of stop/parcel tracking IDs in this cluster.
        vehicles: List of available vehicle IDs assigned to this cluster.
        warehouse_id: Default warehouse ID for departure and return.
        trips_per_vehicle: Number of trips per vehicle (default 1).
        seed: Random seed for reproducibility.

    Returns:
        Valid Chromosome instance.
    """
    if not stops:
        return Chromosome(genes=[])

    if not vehicles:
        vehicles = ["VEH-001"]

    rng = random.Random(seed)
    shuffled_stops = list(stops)
    rng.shuffle(shuffled_stops)

    # Build break markers
    breaks: list[BreakGene] = []
    for trip in range(1, trips_per_vehicle + 1):
        for v_id in vehicles:
            breaks.append(BreakGene(vehicle_id=v_id, trip_number=trip, warehouse_id=warehouse_id))

    # If only 1 subroute / break marker, prefix with break and follow with all stops
    if len(breaks) <= 1:
        genes: list[Gene] = [breaks[0]] if breaks else []
        genes.extend(StopGene(stop_id=s, warehouse_id=warehouse_id) for s in shuffled_stops)
        return Chromosome(genes=genes)

    # Distribute stops among available subroutes (breaks)
    n_stops = len(shuffled_stops)
    n_breaks = len(breaks)

    # Choose split points
    # Pick n_breaks - 1 split points in range [0, n_stops]
    split_indices = sorted(rng.sample(range(n_stops + 1), min(n_breaks - 1, n_stops))) if n_stops > 0 else []
    while len(split_indices) < n_breaks - 1:
        split_indices.append(n_stops)
    split_indices.sort()

    genes = []
    prev_idx = 0
    for b_idx, b_gene in enumerate(breaks):
        genes.append(b_gene)
        end_idx = split_indices[b_idx] if b_idx < len(split_indices) else n_stops
        for s in shuffled_stops[prev_idx:end_idx]:
            genes.append(StopGene(stop_id=s, warehouse_id=b_gene.warehouse_id))
        prev_idx = end_idx

    return Chromosome(genes=genes)


def validate_chromosome(
    chromosome: Chromosome,
    expected_stops: set[str] | list[str],
) -> tuple[bool, str | None]:
    """
    Validate that chromosome references all expected cluster stops exactly once
    with no duplicates or omissions.

    Args:
        chromosome: Chromosome instance to validate.
        expected_stops: Set or list of expected stop IDs.

    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
    """
    expected_set = set(expected_stops)
    actual_stops = chromosome.stops()
    actual_set = set(actual_stops)

    # 1. Duplicate check
    if len(actual_stops) != len(actual_set):
        duplicates = [s for s in actual_set if actual_stops.count(s) > 1]
        return False, f"Duplicate stops in chromosome: {duplicates}"

    # 2. Missing check
    missing = expected_set - actual_set
    if missing:
        return False, f"Missing expected stops in chromosome: {list(missing)}"

    # 3. Unexpected stop check
    extra = actual_set - expected_set
    if extra:
        return False, f"Unexpected extra stops in chromosome: {list(extra)}"

    return True, None
