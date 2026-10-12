"""
backend/app/routers/routing_geometry.py — Road Geometry API for Street-Snapped Route Visualization

Exposes endpoints to fetch high-resolution road polylines from OSRM for vehicle route legs.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.routing.osrm import fetch_osrm_route_geometry

log = logging.getLogger(__name__)

router = APIRouter(prefix="/routing", tags=["Routing Engine"])


class Waypoint(BaseModel):
    lat: float = Field(..., description="Latitude coordinate")
    lon: float = Field(..., description="Longitude coordinate")


class RoadGeometryRequest(BaseModel):
    waypoints: list[Waypoint] = Field(
        ...,
        min_length=2,
        description="Ordered list of route waypoints starting and ending at warehouse or stops",
    )


class RoadGeometryResponse(BaseModel):
    coordinates: list[list[float]] = Field(
        ...,
        description="High-resolution street-snapped coordinates as [[lat, lon], ...]",
    )
    distance_km: float = Field(..., description="Estimated road distance in kilometres")
    duration_min: float = Field(..., description="Estimated road travel duration in minutes")
    source: str = Field(..., description="'osrm' if snapped to streets, 'direct_fallback' otherwise")
    points_count: int = Field(..., description="Total points in the resolved polyline")


@router.post(
    "/road-geometry",
    response_model=RoadGeometryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_road_geometry(req: RoadGeometryRequest) -> Any:
    """
    Given an ordered list of waypoints (e.g. warehouse -> stop 1 -> ... -> stop N -> warehouse),
    returns the exact street-snapped road geometry coordinates, hugging curves, turns, and highways.
    """
    raw_waypoints = [{"lat": wp.lat, "lon": wp.lon} for wp in req.waypoints]
    result = await fetch_osrm_route_geometry(raw_waypoints)
    return result
