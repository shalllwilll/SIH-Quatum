"""
Parcel Pydantic model — spec §7.

Units (spec §3a — hard rule, never store display-formatted strings):
- weight_kg: float (kilograms)
- sla_start_min: int (minutes since midnight, 0–1439)
- sla_deadline_min: int (minutes since midnight, 0–1439)
- node_id: int (OSMnx graph node ID)
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class ParcelStatus(StrEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    DELIVERED = "delivered"
    FAILED = "failed"


class ParcelBase(BaseModel):
    """Fields shared by create and read schemas."""

    address: str = Field(..., min_length=1, description="Delivery address for display")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude (decimal degrees)")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude (decimal degrees)")
    # node_id set after graph snapping
    node_id: int | None = Field(None, description="OSMnx graph node ID (set after graph snap)")

    weight_kg: float = Field(..., gt=0.0, description="Parcel weight in kilograms")

    # SLA window — stored as minutes since midnight (spec §3a)
    sla_start_min: int = Field(
        ..., ge=0, le=1439, description="SLA window open (minutes since midnight)"
    )
    sla_deadline_min: int = Field(
        ..., ge=0, le=1439, description="SLA deadline (minutes since midnight)"
    )

    status: ParcelStatus = Field(ParcelStatus.PENDING, description="Current parcel status")

    @model_validator(mode="after")
    def sla_window_valid(self) -> ParcelBase:
        """Ensure the SLA window is non-empty (deadline strictly after start)."""
        if self.sla_deadline_min <= self.sla_start_min:
            raise ValueError(
                "sla_deadline_min must be strictly greater than sla_start_min"
            )
        return self


class ParcelCreate(ParcelBase):
    """Request schema for creating a parcel."""


class Parcel(ParcelBase):
    """Full parcel document as stored in MongoDB."""

    id: str | None = Field(None, alias="_id", description="MongoDB ObjectId as string")

    model_config = {"populate_by_name": True}
