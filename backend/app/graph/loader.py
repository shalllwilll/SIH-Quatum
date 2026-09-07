"""
backend/app/graph/loader.py — Milestone 1.1

In-memory singleton graph loader for the Pune road network graph.
Loads pune_graph.graphml from backend/data/ using OSMnx / NetworkX.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import networkx as nx

log = logging.getLogger(__name__)

_GRAPH: nx.MultiDiGraph | None = None

DEFAULT_GRAPH_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "pune_graph.graphml"
)


def load_graph(path: Path | str | None = None) -> nx.MultiDiGraph:
    """
    Load the road network graph from disk (.graphml) into memory.

    Args:
        path: Optional custom path to graphml file. If None, defaults to DEFAULT_GRAPH_PATH.

    Returns:
        nx.MultiDiGraph instance.

    Raises:
        FileNotFoundError: If graphml file does not exist.
    """
    global _GRAPH
    import osmnx as ox

    target_path = Path(path) if path else DEFAULT_GRAPH_PATH

    if not target_path.exists():
        raise FileNotFoundError(
            f"Graph cache file not found at '{target_path}'. "
            "Please run 'make build-graph' or 'python -m backend.scripts.build_graph' to generate it."
        )

    log.info("Loading OSM road network graph from %s ...", target_path)
    graph = ox.load_graphml(filepath=target_path)
    _GRAPH = graph
    log.info(
        "Loaded graph successfully: %d nodes, %d edges.",
        graph.number_of_nodes(),
        graph.number_of_edges(),
    )
    return _GRAPH


def get_graph() -> nx.MultiDiGraph:
    """
    Get the in-memory singleton graph instance.
    Loads from DEFAULT_GRAPH_PATH if not already cached.

    Returns:
        nx.MultiDiGraph singleton instance.
    """
    global _GRAPH
    if _GRAPH is None:
        return load_graph()
    return _GRAPH


def reset_graph() -> None:
    """
    Clear the cached graph singleton instance (primarily for unit testing).
    """
    global _GRAPH
    _GRAPH = None
