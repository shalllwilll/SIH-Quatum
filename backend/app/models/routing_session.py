"""
RoutingSession Pydantic model — spec §7.

A RoutingSession records a single run of the QGA+QPSO pipeline:
- which preset was used
- the cluster assignments
- the resulting vehicle route plans
- the fitness/metrics history
- whether it was pre-seeded for demo purposes

Units (spec §3a):
- All time offsets in minutes (int).
- All distances in kilometres (float).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, BaseModel, Field


class SessionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionPreset(StrEnum):
    BALANCED = "balanced"
    MIN_DISTANCE = "min_distance"
    MIN_FUEL = "min_fuel"
    PRIORITIZE_SLA = "prioritize_sla"


class RoutingSessionBase(BaseModel):
    """Core fields for a routing session."""

    preset: SessionPreset = Field(..., description="Business-priority preset used for this run")
    status: SessionStatus = Field(SessionStatus.PENDING, description="Pipeline run status")

    # Set at session creation; wall-clock Unix timestamp (seconds)
    created_at: float = Field(..., description="Unix timestamp (seconds) when session was created")

    # Cluster and vehicle assignment data — populated once pipeline completes
    cluster_count: int | None = Field(None, ge=1, description="Number of Leiden clusters used")
    vehicle_assignments: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Per-vehicle route plans from the pipeline (decoded chromosome output)",
    )

    # QGA convergence data — list of {generation: int, best_fitness: float, avg_fitness: float}
    fitness_history: list[dict[str, Any]] = Field(
        default_factory=list, description="Per-generation fitness history from QGA"
    )

    # Summary metrics — populated at pipeline completion
    total_distance_km: float | None = Field(None, ge=0.0, description="Total route distance (km)")
    sla_compliance_pct: float | None = Field(
        None, ge=0.0, le=100.0, description="SLA compliance percentage for this session"
    )

    # Flag for pre-seeded historical demo sessions (spec §9/10.1)
    seeded: bool = Field(False, description="True if this session was pre-generated for demo purposes")


class RoutingSessionCreate(RoutingSessionBase):
    """Request schema for starting a new routing session."""


class RoutingSession(RoutingSessionBase):
    """Full routing session document as stored in MongoDB."""

    id: str | None = Field(
        None,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
        description="MongoDB ObjectId as string",
    )

    model_config = {"populate_by_name": True}
