"""
Vehicle Pydantic model — spec §7.

Units (spec §3a):
- capacity_kg: float (kilograms)
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import AliasChoices, BaseModel, Field


class VehicleStatus(StrEnum):
    IDLE = "idle"
    EN_ROUTE = "en_route"
    DELIVERING = "delivering"
    COMPLETE = "complete"


class VehicleBase(BaseModel):
    """Fields shared by create and read schemas."""

    label: str = Field(..., min_length=1, description="Human-readable vehicle label (e.g. 'Van-1')")
    capacity_kg: float = Field(..., gt=0.0, description="Maximum load capacity in kilograms")
    status: VehicleStatus = Field(VehicleStatus.IDLE, description="Current vehicle status")

    # Assigned driver account (set by admin in Phase 6/7)
    driver_id: str | None = Field(None, description="Driver account ID assigned to this vehicle")

    # Current warehouse the vehicle is staged at or returning to
    current_warehouse_id: str | None = Field(
        None, description="Warehouse ObjectId string the vehicle is currently assigned to"
    )


class VehicleCreate(VehicleBase):
    """Request schema for creating a vehicle."""


class VehicleUpdate(BaseModel):
    """Request schema for partial vehicle updates."""

    label: str | None = Field(None, min_length=1, description="Human-readable vehicle label")
    capacity_kg: float | None = Field(None, gt=0.0, description="Maximum load capacity in kilograms")
    status: VehicleStatus | None = Field(None, description="Updated vehicle status")
    driver_id: str | None = Field(None, description="Assigned driver account ID")
    current_warehouse_id: str | None = Field(None, description="Assigned warehouse ObjectId")


class Vehicle(VehicleBase):
    """Full vehicle document as stored in MongoDB."""

    id: str | None = Field(
        None,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
        description="MongoDB ObjectId as string",
    )

    model_config = {"populate_by_name": True}
