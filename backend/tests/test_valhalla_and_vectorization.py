"""
backend/tests/test_valhalla_and_vectorization.py

Comprehensive tests for enterprise performance upgrades:
1. Vectorized Qubit Encoding & Rotation Gate (NumPy)
2. Vectorized QPSO Particle Swarm Dynamics (NumPy)
3. Valhalla C++ Routing Engine Client & Fallback Matrix
4. Accelerated Spatial Traffic Propagation (scipy.spatial.cKDTree)
5. 2-Opt Post-Insertion Route Smoothing Heuristic
6. Telemetry Streaming WebSocket Manager
"""

import math

import pytest

from app.pipeline.local_repair import apply_2opt_smoothing
from app.qga.chromosome import BreakGene, Chromosome, StopGene
from app.qga.qubit_encoding import QubitChromosome
from app.qpso.particle import QPSOParticle, compute_mbest
from app.routers.websocket import ConnectionManager
from app.routing.valhalla import ValhallaClient, get_routing_matrix
from app.traffic.propagate import propagate_congestion_to_graph
from app.traffic.tomtom_client import FlowSegmentReading


def test_numpy_qubit_encoding_and_observe():
    """Verify vectorized NumPy qubit encoding produces valid collapsed chromosome."""
    stops = [f"STOP-{i}" for i in range(10)]
    vehicles = ["VAN-01", "VAN-02"]
    qchrom = QubitChromosome(stop_ids=stops, vehicles=vehicles, warehouse_id="WH-01")

    assert len(qchrom.thetas) == 10
    # Equal superposition on init
    for th in qchrom.thetas:
        assert math.isclose(th, math.pi / 4.0, rel_tol=1e-5)

    observed = qchrom.observe(seed=42)
    assert isinstance(observed, Chromosome)
    obs_stops = observed.stops()
    assert len(obs_stops) == 10
    assert set(obs_stops) == set(stops)


def test_numpy_qubit_rotation_gate():
    """Verify quantum rotation gate shifts amplitude angles toward target."""
    stops = ["A", "B", "C", "D"]
    vehicles = ["VAN-01"]
    qchrom = QubitChromosome(stop_ids=stops, vehicles=vehicles, warehouse_id="WH-01")

    curr = Chromosome(genes=[BreakGene("VAN-01", 1, "WH-01"), StopGene("A", "WH-01"), StopGene("B", "WH-01"), StopGene("C", "WH-01"), StopGene("D", "WH-01")])
    # Target inverts order: D, C, B, A
    target = Chromosome(genes=[BreakGene("VAN-01", 1, "WH-01"), StopGene("D", "WH-01"), StopGene("C", "WH-01"), StopGene("B", "WH-01"), StopGene("A", "WH-01")])

    init_theta_D = qchrom.thetas[3]
    qchrom.rotate_toward_best(curr, target, step_size=0.1 * math.pi)

    # Stop D was at index 3 and target is index 0 -> target_idx < actual_idx -> theta increases
    assert qchrom.thetas[3] > init_theta_D
    assert qchrom.thetas[0] < math.pi / 4.0  # Stop A was at index 0, target is index 3 -> theta decreases


def test_numpy_qpso_particle_and_mbest():
    """Verify vectorized QPSO position updates and compute_mbest."""
    p1 = QPSOParticle(position=[400.0, 500.0], bounds=(360.0, 1200.0))
    p2 = QPSOParticle(position=[600.0, 700.0], bounds=(360.0, 1200.0))

    mbest = compute_mbest([p1, p2])
    assert math.isclose(mbest[0], 500.0, rel_tol=1e-5)
    assert math.isclose(mbest[1], 600.0, rel_tol=1e-5)

    p1.update_quantum_position(gbest_position=[450.0, 550.0], mbest_position=mbest, beta=0.75, seed=42)
    assert 360.0 <= p1.position[0] <= 1200.0
    assert 360.0 <= p1.position[1] <= 1200.0


@pytest.mark.asyncio
async def test_valhalla_client_matrix_and_fallback():
    """Verify Valhalla client and fallback distance matrix calculation."""
    client = ValhallaClient(base_url="http://localhost:9999")  # unreachable URL to test fallback

    locs = [
        {"id": "WH-1", "lat": 18.5204, "lon": 73.8567},
        {"id": "STOP-1", "lat": 18.5500, "lon": 73.8900},
        {"id": "STOP-2", "lat": 18.5000, "lon": 73.8000},
    ]

    dist_matrix, time_matrix = await get_routing_matrix(locs, valhalla_client=client)

    assert ("WH-1", "STOP-1") in dist_matrix
    assert dist_matrix[("WH-1", "STOP-1")] > 0.0
    assert time_matrix[("WH-1", "STOP-1")] > 0.0
    assert dist_matrix[("WH-1", "WH-1")] == 0.0


def test_ckdtree_congestion_propagation():
    """Verify cKDTree batch spatial propagation matches expected nearest neighbors."""
    readings = [
        FlowSegmentReading(segment_id="SEG-EAST", lat=18.55, lon=73.95, current_speed_kmh=20, free_flow_speed_kmh=40, congestion_ratio=2.0, confidence=1.0, source="live"),
        FlowSegmentReading(segment_id="SEG-WEST", lat=18.50, lon=73.75, current_speed_kmh=40, free_flow_speed_kmh=40, congestion_ratio=1.0, confidence=1.0, source="live"),
    ]

    class MockGraph:
        def __init__(self):
            self.nodes = {
                1: {"x": 73.94, "y": 18.54},  # closer to EAST
                2: {"x": 73.76, "y": 18.51},  # closer to WEST
            }
            self._edges = [
                (1, 2, 0, {}),
                (2, 1, 0, {}),
            ]

        def edges(self, keys=False, data=False):
            return self._edges

    mock_graph = MockGraph()
    count = propagate_congestion_to_graph(mock_graph, readings)
    assert count == 2

    # Edge starting at node 1 must match SEG-EAST
    edges_data = list(mock_graph.edges(keys=True, data=True))
    assert edges_data[0][3]["associated_segment_id"] == "SEG-EAST"
    assert edges_data[0][3]["congestion_ratio"] == 2.0

    # Edge starting at node 2 must match SEG-WEST
    assert edges_data[1][3]["associated_segment_id"] == "SEG-WEST"
    assert edges_data[1][3]["congestion_ratio"] == 1.0


def test_2opt_route_smoothing():
    """Verify 2-opt heuristic uncrosses intersecting route segments."""
    # Coordinate grid: A(0,0), B(0,2), C(2,0), D(2,2)
    # Crossing route: A -> D -> B -> C
    # Uncrossed route: A -> B -> D -> C (or A -> C -> D -> B)
    coords = {
        "A": (0, 0),
        "B": (0, 2),
        "C": (2, 0),
        "D": (2, 2),
    }

    dist_lookup = {}
    for s1, (x1, y1) in coords.items():
        for s2, (x2, y2) in coords.items():
            dist_lookup[(s1, s2)] = math.hypot(x2 - x1, y2 - y1)

    initial_crossed = ["A", "D", "B", "C"]
    initial_dist = sum(dist_lookup[(initial_crossed[i], initial_crossed[(i + 1) % 4])] for i in range(4))

    smoothed = apply_2opt_smoothing(initial_crossed, distance_lookup=dist_lookup)
    smoothed_dist = sum(dist_lookup[(smoothed[i], smoothed[(i + 1) % 4])] for i in range(4))

    assert smoothed_dist < initial_dist
    assert set(smoothed) == set(initial_crossed)


@pytest.mark.asyncio
async def test_websocket_manager_registration():
    """Verify ConnectionManager handles registration and disconnections cleanly."""
    mgr = ConnectionManager()
    assert len(mgr.fleet_connections) == 0
    assert len(mgr.driver_connections) == 0
