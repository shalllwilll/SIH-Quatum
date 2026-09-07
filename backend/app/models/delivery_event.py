"""
DeliveryEvent Pydantic model — spec §7.

Records an individual delivery outcome (delivered or failed) for a single stop,
linked to a routing session. This is the trigger point for Phase 9's
re-optimization logic.

Units (spec §3a):
- recorded_at_min: int (minutes since midnight, 0–1439) — simulated time of event.
- recorded_at_wall: float (Unix timestamp seconds) — real-world recording time.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DeliveryStatus(StrEnum):
    DELIVERED = "delivered"
    FAILED = "failed"


class DeliveryEventBase(BaseModel):
    """Core fields for a delivery event."""

    routing_session_id: str = Field(
        ..., description="ObjectId of the RoutingSession this event belongs to"
    )
    vehicle_id: str = Field(..., description="ObjectId of the vehicle that attempted delivery")
    parcel_id: str = Field(..., description="ObjectId of the parcel being delivered/failed")

    status: DeliveryStatus = Field(..., description="Outcome: delivered or failed")

    # Simulated time of the event — minutes since midnight (spec §3a)
    recorded_at_min: int = Field(
        ..., ge=0, le=1439, description="Simulated time of event (minutes since midnight)"
    )

    # Real wall-clock Unix timestamp for logging/auditing
    recorded_at_wall: float = Field(..., description="Real Unix timestamp (seconds) of event recording")

    # Optional driver note for failed deliveries
    note: str | None = Field(None, description="Optional note (e.g. failure reason)")


class DeliveryEventCreate(DeliveryEventBase):
    """Request schema for recording a delivery event."""


class DeliveryEvent(DeliveryEventBase):
    """Full delivery event document as stored in MongoDB."""

    id: str | None = Field(None, alias="_id", description="MongoDB ObjectId as string")

    model_config = {"populate_by_name": True}
