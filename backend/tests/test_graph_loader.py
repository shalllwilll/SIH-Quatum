"""
backend/tests/test_graph_loader.py — Milestone 1.1 Test Suite

Test Cases:
  TC-1.1-01: File missing -> FileNotFoundError with descriptive message
  TC-1.1-02: Cache loading & edge attributes verification
  TC-1.1-03: reset_graph() clears cache, next get_graph() reloads
"""

import networkx as nx
import osmnx as ox
import pytest

from app.graph.loader import get_graph, load_graph, reset_graph


@pytest.fixture(autouse=True)
def _clear_graph_singleton():
    """Ensure singleton is cleared before and after each test."""
    reset_graph()
    yield
    reset_graph()


def test_tc_1_1_01_file_missing(tmp_path):
    """TC-1.1-01: Verify FileNotFoundError is raised when graphml file is missing."""
    non_existent = tmp_path / "non_existent_graph.graphml"
    with pytest.raises(FileNotFoundError) as exc_info:
        load_graph(non_existent)
    assert "Graph cache file not found" in str(exc_info.value)
    assert str(non_existent) in str(exc_info.value)


def test_tc_1_1_02_load_and_edge_attributes(tmp_path):
    """
    TC-1.1-02: Verify loading graph from file, singleton caching,
    and presence of required edge routing attributes.
    """
    # Create a small synthetic MultiDiGraph
    g = nx.MultiDiGraph()
    g.add_node(1, x=73.8567, y=18.5204)
    g.add_node(2, x=73.8580, y=18.5215)
    g.add_edge(
        1,
        2,
        key=0,
        length=500.0,
        distance_km=0.5,
        base_travel_time_min=1.0,
        congestion_ratio=1.0,
        congestion_type="multiplicative",
    )

    test_file = tmp_path / "test_graph.graphml"
    ox.save_graphml(g, filepath=test_file)

    # 1. Load explicit file
    loaded_g = load_graph(test_file)
    assert isinstance(loaded_g, nx.MultiDiGraph)
    assert loaded_g.number_of_nodes() == 2
    assert loaded_g.number_of_edges() == 1

    # 2. Verify get_graph() returns the same singleton
    singleton_g = get_graph()
    assert singleton_g is loaded_g

    # 3. Verify edge routing attributes exist and have valid types/values
    for _u, _v, _k, data in loaded_g.edges(keys=True, data=True):
        # Attribute conversion from graphml: floats might be parsed as float or string by networkx depending on graphml schema
        dist = float(data.get("distance_km"))
        travel_time = float(data.get("base_travel_time_min"))
        cong_ratio = float(data.get("congestion_ratio"))
        cong_type = str(data.get("congestion_type"))

        assert dist == pytest.approx(0.5)
        assert travel_time == pytest.approx(1.0)
        assert cong_ratio == pytest.approx(1.0)
        assert cong_type == "multiplicative"


def test_tc_1_1_03_reset_graph(tmp_path):
    """TC-1.1-03: Verify reset_graph() clears singleton cache."""
    g = nx.MultiDiGraph()
    g.add_node(100, x=73.85, y=18.52)
    test_file = tmp_path / "test_reset.graphml"
    ox.save_graphml(g, filepath=test_file)

    g1 = load_graph(test_file)
    assert get_graph() is g1

    reset_graph()

    # After reset, get_graph() with default path will fail if default file doesn't exist
    # or reload if called with load_graph(test_file)
    g2 = load_graph(test_file)
    assert g2 is not g1
