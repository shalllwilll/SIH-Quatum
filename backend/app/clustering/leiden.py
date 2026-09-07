"""
backend/app/clustering/leiden.py — Milestone 2.2

Leiden community-detection pre-clustering module per spec §3d.
Partitions active delivery stops into geographically and network-coherent clusters
before handing them to QGA (Phase 3) for route optimization.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class ClusteringResult:
    """Encapsulates the output of Leiden pre-clustering."""
    clusters: dict[int, list[dict[str, Any]]]
    assignments: dict[str, int]
    cluster_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


def _haversine_distance_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate great-circle distance between two coordinate pairs in kilometres."""
    r = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def cluster_stops(
    parcels: list[dict[str, Any]],
    warehouses: list[dict[str, Any]] | None = None,
    resolution: float = 1.0,
    k_neighbors: int = 8,
    seed: int | None = 42,
    min_cluster_threshold: int = 4,
) -> ClusteringResult:
    """
    Cluster delivery stops into geographically coherent groups using Leiden algorithm.

    Args:
        parcels: List of parcel dictionaries containing tracking_number and location (GeoJSON Point).
        warehouses: Optional list of warehouse dictionaries.
        resolution: Leiden resolution parameter (controls cluster granularity).
        k_neighbors: Number of nearest neighbors to connect in proximity graph.
        seed: Random seed for deterministic reproducibility.
        min_cluster_threshold: Minimum number of parcels below which clustering falls back to 1 cluster.

    Returns:
        ClusteringResult dataclass instance.
    """
    t0 = time.perf_counter()

    if not parcels:
        return ClusteringResult(
            clusters={},
            assignments={},
            cluster_count=0,
            metadata={"runtime_ms": 0.0, "reason": "empty_input"},
        )

    n_parcels = len(parcels)

    # Degenerate case: very few parcels
    if n_parcels < min_cluster_threshold:
        assignments = {p.get("tracking_number", f"PARCEL-{i}"): 0 for i, p in enumerate(parcels)}
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return ClusteringResult(
            clusters={0: list(parcels)},
            assignments=assignments,
            cluster_count=1,
            metadata={"runtime_ms": elapsed_ms, "fallback": "small_input"},
        )

    import igraph as ig
    import leidenalg

    # Extract coordinates
    coords = []
    keys = []
    for i, p in enumerate(parcels):
        key = p.get("tracking_number") or p.get("parcel_id") or f"P-{i}"
        loc = p.get("location", {})
        c = loc.get("coordinates", [73.8567, 18.5204])
        lon, lat = float(c[0]), float(c[1])
        coords.append((lon, lat))
        keys.append(key)

    # Build k-NN proximity graph with inverse-distance weights
    k = min(k_neighbors, n_parcels - 1)
    edges = []
    weights = []
    added_pairs = set()

    for i in range(n_parcels):
        lon_i, lat_i = coords[i]
        # Compute distances to all other nodes
        dists = []
        for j in range(n_parcels):
            if i != j:
                lon_j, lat_j = coords[j]
                d = _haversine_distance_km(lon_i, lat_i, lon_j, lat_j)
                dists.append((d, j))

        dists.sort(key=lambda x: x[0])
        # Connect to k nearest
        for d, j in dists[:k]:
            pair = (min(i, j), max(i, j))
            if pair not in added_pairs:
                added_pairs.add(pair)
                edges.append(pair)
                # Inverse distance weight with smoothing epsilon (0.2 km)
                w = 1.0 / (d + 0.2)
                weights.append(w)

    # Build igraph Graph
    g = ig.Graph(n=n_parcels, edges=edges)
    g.es["weight"] = weights

    # Run Leiden algorithm
    if seed is not None:
        partition = leidenalg.find_partition(
            g,
            leidenalg.RBConfigurationVertexPartition,
            weights=weights,
            resolution_parameter=resolution,
            seed=seed,
        )
    else:
        partition = leidenalg.find_partition(
            g,
            leidenalg.RBConfigurationVertexPartition,
            weights=weights,
            resolution_parameter=resolution,
        )

    membership = partition.membership

    # Group into clusters
    clusters: dict[int, list[dict[str, Any]]] = {}
    assignments: dict[str, int] = {}

    for idx, cluster_id in enumerate(membership):
        parcel = parcels[idx]
        key = keys[idx]

        assignments[key] = cluster_id
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(parcel)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    log.info(
        "Leiden clustering: %d parcels -> %d clusters in %.2fms (resolution=%.2f, seed=%s)",
        n_parcels,
        len(clusters),
        elapsed_ms,
        resolution,
        seed,
    )

    return ClusteringResult(
        clusters=clusters,
        assignments=assignments,
        cluster_count=len(clusters),
        metadata={
            "runtime_ms": elapsed_ms,
            "resolution": resolution,
            "seed": seed,
            "node_count": n_parcels,
            "edge_count": len(edges),
        },
    )
