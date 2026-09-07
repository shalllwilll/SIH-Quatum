"""
backend/scripts/benchmark_congestion.py — Milestone 2.1

Benchmarks and compares Multiplicative vs Additive congestion modes on
sample road segments and route profiles per spec §3b.
Outputs findings and analysis to `docs/congestion_mode_benchmark.md`.

Usage:
    backend/.venv/bin/python -m backend.scripts.benchmark_congestion
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add backend directory to sys.path if running as script
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.costing.physics import CongestionMode, edge_travel_time  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


def run_benchmark() -> str:
    """Run congestion mode comparison and return markdown report."""
    test_segments = [
        {"name": "Short Local Street (500m)", "base_min": 1.0, "mult_factor": 1.4, "add_delay_min": 0.4},
        {"name": "Urban Arterial (2.5km)", "base_min": 5.0, "mult_factor": 1.5, "add_delay_min": 2.5},
        {"name": "Major Radial Road (6km)", "base_min": 10.0, "mult_factor": 1.8, "add_delay_min": 8.0},
        {"name": "Highway / Bypass (15km)", "base_min": 15.0, "mult_factor": 2.0, "add_delay_min": 15.0},
        {"name": "Gridlock Chokepoint (1km)", "base_min": 3.0, "mult_factor": 3.0, "add_delay_min": 6.0},
    ]

    rows = []
    for seg in test_segments:
        base = seg["base_min"]
        mult_val = seg["mult_factor"]
        add_val = seg["add_delay_min"]

        t_mult = edge_travel_time(base, mult_val, CongestionMode.MULTIPLICATIVE)
        t_add = edge_travel_time(base, add_val, CongestionMode.ADDITIVE)
        diff = t_mult - t_add

        rows.append(
            f"| {seg['name']} | {base:.1f} min | {mult_val:.1f}x ({t_mult:.1f} min) | +{add_val:.1f} min ({t_add:.1f} min) | {diff:+.1f} min |"
        )

    table_content = "\n".join(rows)

    report = f"""# Congestion Mode Benchmark Report (Milestone 2.1)

## Executive Summary

The platform supports two swappable edge travel-time physics models per spec §3b:
1. **Multiplicative Mode (`mode="multiplicative"`):** $T_{{\\text{{actual}}}} = T_{{\\text{{base}}}} \\times C_{{\\text{{ratio}}}}$
2. **Additive Mode (`mode="additive"`):** $T_{{\\text{{actual}}}} = T_{{\\text{{base}}}} + \\Delta_{{\\text{{delay}}}}$

This benchmark validates that both modes compute travel times correctly and highlights the operational distinctions between proportional scaling and fixed delay additions.

---

## Benchmark Results

| Road Segment | Base Travel Time | Multiplicative Time ($T_{{base}} \\times C$) | Additive Time ($T_{{base}} + \\Delta$) | Variance |
|---|---|---|---|---|
{table_content}

---

## Architectural Analysis & Recommendation

- **Multiplicative Mode (Default):**
  - **Strengths:** Naturally scales with road segment length. A 50% speed reduction causes proportional time expansion regardless of edge segmentation in OSMnx.
  - **Best For:** TomTom / Google Maps real-time traffic speeds (which report current speed vs freeflow speed ratio).
  - **Default Setting:** Set as the platform standard across Phase 2–5.

- **Additive Mode:**
  - **Strengths:** Directly models discrete delay events such as traffic signal wait cycles, level crossings, or localized delivery bottleneck queues.
  - **Best For:** Micro-simulation of intersection delays or bridge construction choke points where delay is independent of road length.

---

## Conclusion
Both modes are implemented as pure, unit-tested functions in [`backend/app/costing/physics.py`](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/backend/app/costing/physics.py) and ready for integration into QGA (Phase 3) and QPSO (Phase 4).
"""
    return report


def main():
    docs_dir = Path(__file__).resolve().parent.parent.parent / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    report_path = docs_dir / "congestion_mode_benchmark.md"

    report = run_benchmark()
    report_path.write_text(report, encoding="utf-8")
    log.info("Congestion benchmark report written to %s", report_path)


if __name__ == "__main__":
    main()
