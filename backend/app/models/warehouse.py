"""
Warehouse Pydantic model — spec §7.

Units (spec §3a):
- Coordinates stored as float (decimal degrees).
- node_id stored as int (OSMnx graph node ID).
"""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field


class WarehouseBase(BaseModel):
    """Fields shared by create and read schemas."""

    name: str = Field(..., min_length=1, description="Human-readable warehouse name")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude (decimal degrees)")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude (decimal degrees)")
    address: str = Field(..., min_length=1, description="Street address for display")
    # node_id is set after graph snapping; optional at creation time
    node_id: int | None = Field(None, description="OSMnx graph node ID (set after graph snap)")


class WarehouseCreate(WarehouseBase):
    """Request schema for creating a warehouse."""


class Warehouse(WarehouseBase):
    """Full warehouse document as stored in MongoDB."""

    id: str | None = Field(
        None,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
        description="MongoDB ObjectId as string",
    )

    model_config = {"populate_by_name": True}
