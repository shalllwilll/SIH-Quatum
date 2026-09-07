"""
backend/tests/test_stops.py — Milestone 1.2 Test Suite

Test Cases:
  TC-1.2-01: Warehouses seeded with valid graph node IDs
  TC-1.2-02: Parcels seeded (100–120 count) with valid node IDs & canonical units
  TC-1.2-03: All stops reachable from at least one warehouse
  TC-1.2-04: Unreachable stop flagged/rejected by validator (negative test)
  TC-1.2-05: Boundary SLA windows strictly in [0, 1439] with start < end
  TC-1.2-06: Deterministic regeneration produces identical dataset
"""

import networkx as nx
import pytest

from scripts.generate_stops import generate_seed_data
from scripts.validate_stops import validate_stops_in_memory


@pytest.fixture(scope="module")
def sample_graph():
    """Create a synthetic directed graph with connected and isolated components for testing."""
    g = nx.MultiDiGraph()
    g.graph["crs"] = "epsg:4326"
    # Connected component: nodes 1, 2, 3, 4, 5
    # Node 1: Warehouse
    g.add_node(1, x=73.8475, y=18.5308)
    g.add_node(2, x=73.8500, y=18.5320)
    g.add_node(3, x=73.8520, y=18.5340)
    g.add_node(4, x=73.8540, y=18.5360)
    g.add_node(5, x=73.8560, y=18.5380)

    g.add_edge(1, 2, key=0, distance_km=0.5, base_travel_time_min=1.0)
    g.add_edge(2, 3, key=0, distance_km=0.6, base_travel_time_min=1.2)
    g.add_edge(3, 4, key=0, distance_km=0.7, base_travel_time_min=1.4)
    g.add_edge(4, 5, key=0, distance_km=0.8, base_travel_time_min=1.6)
    # Return edges to make strongly connected
    g.add_edge(5, 1, key=0, distance_km=2.6, base_travel_time_min=5.2)

    # Isolated component: node 999
    g.add_node(999, x=73.9999, y=18.9999)

    return g


def test_tc_1_2_01_and_02_seed_generation(sample_graph, monkeypatch):
    """TC-1.2-01 & TC-1.2-02: Verify warehouse and parcel generation attributes."""
    # Patch get_graph to return sample_graph
    monkeypatch.setattr("scripts.generate_stops.get_graph", lambda: sample_graph)

    warehouses, parcels = generate_seed_data(seed=42, num_parcels=10)

    # TC-1.2-01: Warehouses
    assert len(warehouses) == 4
    for wh in warehouses:
        assert wh["warehouse_id"].startswith("WH-PUNE-")
        assert wh["snapped_node_id"] in sample_graph
        assert wh["operating_hours"]["start_time"] < wh["operating_hours"]["end_time"]

    # TC-1.2-02: Parcels
    assert len(parcels) == 10
    for p in parcels:
        assert p["tracking_number"].startswith("PAR-PUNE-")
        assert p["snapped_node_id"] in sample_graph
        assert 1.0 <= p["weight_kg"] <= 15.0
        assert "length" in p["dimensions_cm"]
        sla = p["sla_window"]
        assert 0 <= sla["start_time"] < sla["end_time"] <= 1439


def test_tc_1_2_03_all_stops_reachable(sample_graph, monkeypatch):
    """TC-1.2-03: Verify all generated stops in SCC are reachable."""
    monkeypatch.setattr("scripts.generate_stops.get_graph", lambda: sample_graph)

    warehouses, parcels = generate_seed_data(seed=42, num_parcels=5)
    is_valid, errors = validate_stops_in_memory(sample_graph, warehouses, parcels)

    assert is_valid, f"Validation failed with errors: {errors}"
    assert len(errors) == 0


def test_tc_1_2_04_unreachable_stop_rejected(sample_graph, monkeypatch):
    """TC-1.2-04 (Negative): Verify isolated/unreachable stop is flagged by validator."""
    monkeypatch.setattr("scripts.generate_stops.get_graph", lambda: sample_graph)

    warehouses, parcels = generate_seed_data(seed=42, num_parcels=5)

    # Inject an unreachable parcel at isolated node 999
    parcels.append({
        "tracking_number": "PAR-PUNE-BAD999",
        "recipient": "Unreachable Recipient",
        "address": "Isolated Island, Pune",
        "location": {"type": "Point", "coordinates": [73.9999, 18.9999]},
        "snapped_node_id": 999,
        "warehouse_id": "WH-PUNE-001",
        "weight_kg": 5.0,
        "dimensions_cm": {"length": 20, "width": 15, "height": 10},
        "sla_window": {"start_time": 540, "end_time": 660},
        "priority": "medium",
        "status": "pending",
    })

    is_valid, errors = validate_stops_in_memory(sample_graph, warehouses, parcels)

    assert not is_valid
    assert any("UNREACHABLE" in err for err in errors)


def test_tc_1_2_05_boundary_sla_windows(sample_graph, monkeypatch):
    """TC-1.2-05 (Edge Case): Verify SLA window boundaries and negative validation."""
    monkeypatch.setattr("scripts.generate_stops.get_graph", lambda: sample_graph)

    warehouses, parcels = generate_seed_data(seed=42, num_parcels=5)

    # Inject invalid SLA window (end < start)
    parcels.append({
        "tracking_number": "PAR-PUNE-BADSLA",
        "recipient": "Bad SLA Recipient",
        "address": "Invalid Time Street, Pune",
        "location": {"type": "Point", "coordinates": [73.8500, 18.5320]},
        "snapped_node_id": 2,
        "warehouse_id": "WH-PUNE-001",
        "weight_kg": 5.0,
        "dimensions_cm": {"length": 20, "width": 15, "height": 10},
        "sla_window": {"start_time": 800, "end_time": 600},  # Invalid!
        "priority": "medium",
        "status": "pending",
    })

    is_valid, errors = validate_stops_in_memory(sample_graph, warehouses, parcels)
    assert not is_valid
    assert any("invalid SLA window" in err for err in errors)


def test_tc_1_2_06_deterministic_regeneration(sample_graph, monkeypatch):
    """TC-1.2-06: Verify seed generation is 100% deterministic with same seed."""
    monkeypatch.setattr("scripts.generate_stops.get_graph", lambda: sample_graph)

    wh1, p1 = generate_seed_data(seed=123, num_parcels=20)
    wh2, p2 = generate_seed_data(seed=123, num_parcels=20)

    assert wh1 == wh2
    assert p1 == p2
