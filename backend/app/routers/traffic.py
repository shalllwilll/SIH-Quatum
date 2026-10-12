"""
backend/app/routers/traffic.py — Live Traffic Telemetry & Diagnostics Endpoint

Exposes real-time TomTom traffic status, edge congestion propagation metrics,
and manual refresh triggers for the dispatcher diagnostics portal.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.traffic import get_traffic_manager

router = APIRouter(prefix="/traffic", tags=["Traffic & Diagnostics"])


class SegmentReadingModel(BaseModel):
    segment_id: str
    lat: float
    lon: float
    current_speed_kmh: float
    free_flow_speed_kmh: float
    congestion_ratio: float
    source: str


class TrafficStatusResponse(BaseModel):
    configured: bool
    traffic_source: str
    total_segments: int
    cached_readings_count: int
    last_refresh_epoch: float | None = None
    server_time_iso: str
    sample_segments: list[SegmentReadingModel] = Field(default_factory=list)


@router.get("/status", response_model=TrafficStatusResponse, status_code=status.HTTP_200_OK)
async def get_traffic_status() -> TrafficStatusResponse:
    """
    Get live TomTom traffic integration status and active segment readings.
    """
    manager = get_traffic_manager()
    readings = manager.get_current_readings()

    # Prioritize simulated disturbances and high congestion corridors at top of telemetry
    sorted_readings = sorted(
        readings,
        key=lambda r: (0 if r.source == "simulated_disturbance" else (1 if r.congestion_ratio > 1.3 else 2)),
    )

    sample_items = [
        SegmentReadingModel(
            segment_id=r.segment_id,
            lat=r.lat,
            lon=r.lon,
            current_speed_kmh=r.current_speed_kmh,
            free_flow_speed_kmh=r.free_flow_speed_kmh,
            congestion_ratio=round(r.congestion_ratio, 2),
            source=r.source,
        )
        for r in sorted_readings[:12]  # Top representative arterial corridors
    ]


    return TrafficStatusResponse(
        configured=manager.client.is_configured(),
        traffic_source=manager.cache.traffic_source,
        total_segments=len(manager.segments),
        cached_readings_count=len(readings),
        last_refresh_epoch=manager.cache.last_cycle_timestamp,
        server_time_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        sample_segments=sample_items,
    )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def trigger_traffic_refresh() -> dict[str, Any]:
    """
    Trigger an immediate on-demand TomTom flow polling cycle.
    """
    manager = get_traffic_manager()
    cycle_res = await manager.refresh_cycle()
    return {
        "message": "Traffic refresh cycle executed.",
        "details": cycle_res,
    }
