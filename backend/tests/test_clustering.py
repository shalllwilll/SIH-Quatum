"""
backend/tests/test_clustering.py — Milestone 2.2 Test Suite

Test Cases:
  TC-2.2-01: Clusters produced for full stop set (100–120 stops seeded)
  TC-2.2-02: Every stop assigned to exactly one cluster
  TC-2.2-03: Very few active stops fallback to single cluster (edge case)
  TC-2.2-04: Empty stop set handled gracefully (negative test)
  TC-2.2-05: Deterministic clustering with fixed seed
  TC-2.2-06: Resolution parameter variation adjusts cluster granularity
"""

import random

from app.clustering.leiden import ClusteringResult, cluster_stops


def _generate_synthetic_parcels(count: int, seed: int = 42) -> list[dict]:
    """Helper to generate realistic spatial parcel locations in Pune."""
    rng = random.Random(seed)
    parcels = []
    for i in range(count):
        lon = rng.uniform(73.75, 73.95)
        lat = rng.uniform(18.45, 18.65)
        parcels.append({
            "tracking_number": f"PAR-PUNE-{i:04d}",
            "location": {"type": "Point", "coordinates": [lon, lat]},
            "weight_kg": round(rng.uniform(1.0, 15.0), 1),
            "priority": "medium",
        })
    return parcels


def test_tc_2_2_01_and_02_full_clustering():
    """
    TC-2.2-01 & TC-2.2-02: Verify clustering of full 110-stop dataset.
    Confirms 2+ clusters created and every parcel assigned exactly once.
    """
    parcels = _generate_synthetic_parcels(110, seed=42)
    result = cluster_stops(parcels, resolution=1.0, seed=42)

    assert isinstance(result, ClusteringResult)
    # TC-2.2-01: 2+ clusters produced
    assert result.cluster_count >= 2
    assert len(result.clusters) == result.cluster_count

    # TC-2.2-02: Every stop assigned exactly once
    assert len(result.assignments) == 110
    total_parcels_in_clusters = sum(len(p_list) for p_list in result.clusters.values())
    assert total_parcels_in_clusters == 110

    # Ensure no parcel is duplicated across clusters
    seen_trackings = set()
    for cluster_id, cluster_parcels in result.clusters.items():
        for p in cluster_parcels:
            tn = p["tracking_number"]
            assert tn not in seen_trackings, f"Parcel {tn} appears in multiple clusters"
            seen_trackings.add(tn)
            assert result.assignments[tn] == cluster_id


def test_tc_2_2_03_small_input_fallback():
    """TC-2.2-03 (Edge Case): 3 parcels fallback to single cluster without crashing."""
    parcels = _generate_synthetic_parcels(3, seed=42)
    result = cluster_stops(parcels, resolution=1.0, seed=42, min_cluster_threshold=4)

    assert result.cluster_count == 1
    assert len(result.clusters[0]) == 3
    for p in parcels:
        assert result.assignments[p["tracking_number"]] == 0


def test_tc_2_2_04_empty_input_handled():
    """TC-2.2-04 (Negative): Empty stop set handled gracefully."""
    result = cluster_stops([])

    assert result.cluster_count == 0
    assert result.clusters == {}
    assert result.assignments == {}


def test_tc_2_2_05_deterministic_clustering():
    """TC-2.2-05: Fixed seed produces identical cluster assignments across runs."""
    parcels = _generate_synthetic_parcels(60, seed=123)

    res1 = cluster_stops(parcels, resolution=1.0, seed=42)
    res2 = cluster_stops(parcels, resolution=1.0, seed=42)

    assert res1.cluster_count == res2.cluster_count
    assert res1.assignments == res2.assignments


def test_tc_2_2_06_resolution_granularity():
    """TC-2.2-06: Higher resolution produces finer (more) clusters."""
    parcels = _generate_synthetic_parcels(80, seed=42)

    res_low = cluster_stops(parcels, resolution=0.5, seed=42)
    res_high = cluster_stops(parcels, resolution=2.0, seed=42)

    # Higher resolution parameter in Leiden should produce more or equal number of communities
    assert res_high.cluster_count >= res_low.cluster_count
