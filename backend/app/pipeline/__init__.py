"""
Pipeline package — Milestone 4.3.
Orchestrates end-to-end multi-stage routing optimization (Leiden + QGA + QPSO + Bounce-Back).
"""

from app.pipeline.orchestrator import PipelineResult, run_hybrid_routing_pipeline

__all__ = ["PipelineResult", "run_hybrid_routing_pipeline"]
