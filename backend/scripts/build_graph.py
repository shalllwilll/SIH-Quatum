"""
backend/scripts/build_graph.py — Milestone 1.1

One-time developer script: fetches the Pune road network from OpenStreetMap
via OSMnx, tags every edge with derived routing attributes, and saves the
result to `backend/data/pune_graph.graphml`.

This script MUST be run explicitly by a developer (or CI) — it is NEVER run
automatically at backend startup. The cache file is gitignored and regenerable
at any time by re-running this script.

Spec references:
  §1 — road network graph (drive network, OSMnx)
  §3a — distance in km, time in minutes (canonical units)
  §8  — graph must be pre-cached, never live-fetched during demo

Usage (from repo root):
    backend/.venv/bin/python -m backend.scripts.build_graph
  or via Makefile (to be added):
    make build-graph

Speed fallback table (used when OSM maxspeed tag is missing):
  motorway / motorway_link    : 80 km/h
  trunk / trunk_link          : 60 km/h
  primary / primary_link      : 50 km/h
  secondary / secondary_link  : 40 km/h
  tertiary / tertiary_link    : 30 km/h
  residential                 : 25 km/h
  living_street               : 15 km/h
  service / unclassified      : 20 km/h
  default (anything else)     : 30 km/h
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Speed fallback table — km/h (spec §3a: base_travel_time_min uses km/h)
# ---------------------------------------------------------------------------
_SPEED_FALLBACK_KMH: dict[str, float] = {
    "motorway": 80.0,
    "motorway_link": 80.0,
    "trunk": 60.0,
    "trunk_link": 60.0,
    "primary": 50.0,
    "primary_link": 50.0,
    "secondary": 40.0,
    "secondary_link": 40.0,
    "tertiary": 30.0,
    "tertiary_link": 30.0,
    "residential": 25.0,
    "living_street": 15.0,
    "service": 20.0,
    "unclassified": 20.0,
}
_DEFAULT_SPEED_KMH = 30.0


def _speed_for_edge(highway_tag: str | list | None, maxspeed_tag: str | None) -> float:
    """
    Resolve edge speed in km/h.

    Priority:
      1. OSM maxspeed tag (parsed from strings like "50" or "50 mph")
      2. Fallback table keyed by highway type
      3. Hard default (30 km/h)

    Args:
        highway_tag: OSM highway tag value (may be a list if multiple tags).
        maxspeed_tag: OSM maxspeed tag value (string or None).

    Returns:
        Speed in km/h (always a positive float, never None/NaN).
    """
    # 1. Try to parse maxspeed
    if maxspeed_tag:
        try:
            raw = str(maxspeed_tag).strip().lower()
            if "mph" in raw:
                numeric = float(raw.replace("mph", "").strip())
                return numeric * 1.60934
            return float(raw.split()[0])
        except (ValueError, IndexError):
            pass

    # 2. Fallback by highway type
    if highway_tag:
        tags = highway_tag if isinstance(highway_tag, list) else [highway_tag]
        for tag in tags:
            if tag in _SPEED_FALLBACK_KMH:
                return _SPEED_FALLBACK_KMH[tag]

    return _DEFAULT_SPEED_KMH


def _tag_edges(graph) -> None:
    """
    Add routing attributes to every edge in-place.

    Attributes added (spec §1, §3a):
      distance_km        : float — edge length in kilometres (canonical unit)
      base_travel_time_min : float — uncongested travel time in minutes (canonical unit)
      congestion_ratio   : float — placeholder 1.0 (real values in Phase 5)
      congestion_type    : str   — "multiplicative" (default, per spec §3b)

    Both `distance_km` and `base_travel_time_min` are guaranteed non-None/non-NaN.
    """
    import math

    missing_speed_count = 0
    total_edges = 0

    for _u, _v, _key, data in graph.edges(keys=True, data=True):
        total_edges += 1

        # OSMnx stores length in metres — convert to km (spec §3a)
        length_m: float = data.get("length", 0.0) or 0.0
        distance_km = length_m / 1000.0

        highway = data.get("highway")
        maxspeed = data.get("maxspeed")

        if not maxspeed:
            missing_speed_count += 1

        speed_kmh = _speed_for_edge(highway, maxspeed)

        # base_travel_time_min = distance_km / speed_kmh * 60
        # Guard against zero-length edges
        if distance_km > 0 and speed_kmh > 0:
            base_travel_time_min = distance_km / speed_kmh * 60.0
        else:
            base_travel_time_min = 0.0

        # Sanity guard: ensure no NaN or Inf
        if not math.isfinite(base_travel_time_min):
            base_travel_time_min = 0.0

        data["distance_km"] = distance_km
        data["base_travel_time_min"] = base_travel_time_min
        data["congestion_ratio"] = 1.0          # Phase 5 will set real values
        data["congestion_type"] = "multiplicative"  # spec §3b default

    log.info(
        "Edge tagging complete: %d total edges, %d (%.1f%%) had no maxspeed tag "
        "(fallback applied).",
        total_edges,
        missing_speed_count,
        100.0 * missing_speed_count / total_edges if total_edges else 0,
    )


def build(output_path: Path | None = None) -> Path:
    """
    Fetch the Pune drive network, tag edges, and save to .graphml.

    Args:
        output_path: Override output path (default: backend/data/pune_graph.graphml).

    Returns:
        Path to the saved .graphml file.
    """
    import osmnx as ox

    if output_path is None:
        output_path = (
            Path(__file__).resolve().parent.parent / "data" / "pune_graph.graphml"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Fetching Pune, India road network from OSM (this may take 1–5 minutes)...")
    t0 = time.perf_counter()

    graph = ox.graph_from_place("Pune, India", network_type="drive", simplify=True)

    elapsed = time.perf_counter() - t0
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()
    log.info(
        "Graph fetched in %.1fs: %d nodes, %d edges.", elapsed, node_count, edge_count
    )

    # Sanity check connectivity
    import networkx as nx
    scc_sizes = [len(c) for c in nx.strongly_connected_components(graph)]
    largest_scc = max(scc_sizes)
    coverage_pct = 100.0 * largest_scc / node_count if node_count else 0
    log.info(
        "Connectivity: largest SCC = %d nodes (%.1f%% of total). "
        "%s",
        largest_scc,
        coverage_pct,
        "OK" if coverage_pct >= 80 else "WARNING: low connectivity — review graph area",
    )

    # Tag all edges
    log.info("Tagging edges with distance_km, base_travel_time_min, congestion_* ...")
    _tag_edges(graph)

    # Save to disk
    log.info("Saving graph to %s ...", output_path)
    t1 = time.perf_counter()
    ox.save_graphml(graph, filepath=output_path)
    log.info("Saved in %.1fs.", time.perf_counter() - t1)

    return output_path


if __name__ == "__main__":
    saved = build()
    log.info("Done. Graph saved to: %s", saved)
    sys.exit(0)
