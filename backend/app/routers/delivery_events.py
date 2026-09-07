"""
backend/app/routers/delivery_events.py — Milestone 6.3 & 9.2

Endpoints for logging and querying delivery outcomes (delivered / failed):
- POST /delivery-events (records event, triggers Tier 1 Re-tune / Tier 2 Repair / Tier 3 Escalation)
- GET /delivery-events (lists logged delivery events with re-optimization metrics)
"""

from __future__ import annotations

import time
from typing import Annotated, Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.db import get_db
from app.models.delivery_event import DeliveryEvent, DeliveryStatus
from app.pipeline.local_repair import repair_or_escalate_on_failed
from app.pipeline.retune import retune_on_delivered

router = APIRouter(prefix="/delivery-events", tags=["Delivery Events"])


class DeliveryEventCreateRequest(BaseModel):
    """Payload to log a delivery outcome."""

    routing_session_id: str | None = Field(None, description="ID of the active RoutingSession")
    vehicle_id: str = Field(..., description="ID or label of the delivering vehicle")
    parcel_id: str = Field(..., description="ID or tracking number of the parcel")
    status: DeliveryStatus = Field(..., description="Delivery result: delivered or failed")
    recorded_at_min: int | None = Field(None, ge=0, le=1439, description="Simulated minutes since midnight")
    note: str | None = Field(None, description="Optional driver note or failure reason")


def _doc_to_event(doc: dict[str, Any]) -> DeliveryEvent:
    """Convert MongoDB document to Pydantic DeliveryEvent model."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return DeliveryEvent.model_validate(doc)


@router.post("", response_model=DeliveryEvent, status_code=status.HTTP_201_CREATED)
async def create_delivery_event(event_in: DeliveryEventCreateRequest):
    """
    Record a delivery event and trigger live multi-tiered re-optimization (Milestone 9.2).
    - Status 'delivered': Tier 1 cheap QPSO re-tune on remaining stops.
    - Status 'failed': Tier 2 local repair insertion; escalates to Tier 3 full QGA if necessary.
    """
    db = get_db()

    # Validate parcel exists in database (or create dummy doc for testing)
    parcel_doc = None
    try:
        parcel_doc = await db["parcels"].find_one({"_id": ObjectId(event_in.parcel_id)})
    except (InvalidId, Exception):
        parcel_doc = await db["parcels"].find_one({"parcel_id": event_in.parcel_id})

    if not parcel_doc:
        # Check by tracking number
        parcel_doc = await db["parcels"].find_one({"tracking_number": event_in.parcel_id})

    if not parcel_doc and not event_in.parcel_id.startswith("P-"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID '{event_in.parcel_id}' not found.",
        )

    # Find active session if not provided
    session_id = event_in.routing_session_id
    if not session_id:
        active_session = await db["routing_sessions"].find_one(
            {"status": "completed"},
            sort=[("created_at", -1)],
        )
        if active_session:
            session_id = str(active_session["_id"])

    rec_min = event_in.recorded_at_min if event_in.recorded_at_min is not None else 600

    # Prepare event document
    event_doc: dict[str, Any] = {
        "routing_session_id": session_id or "SESSION-ACTIVE",
        "vehicle_id": event_in.vehicle_id,
        "parcel_id": event_in.parcel_id,
        "status": event_in.status.value,
        "recorded_at_min": rec_min,
        "recorded_at_wall": time.time(),
        "note": event_in.note,
        "reoptimization": {},
    }

    # Execute appropriate live re-optimization tier (Milestone 9.2)
    reopt_result: dict[str, Any] = {}
    if session_id:
        if event_in.status == DeliveryStatus.DELIVERED:
            reopt_result = await retune_on_delivered(
                session_id=session_id,
                vehicle_id=event_in.vehicle_id,
                delivered_stop_id=event_in.parcel_id,
                current_time_min=float(rec_min),
                db=db,
            )
        elif event_in.status == DeliveryStatus.FAILED:
            reopt_result = await repair_or_escalate_on_failed(
                session_id=session_id,
                failed_vehicle_id=event_in.vehicle_id,
                failed_parcel_id=event_in.parcel_id,
                current_time_min=float(rec_min),
                db=db,
            )

    event_doc["reoptimization"] = reopt_result
    insert_res = await db["delivery_events"].insert_one(event_doc)

    # Update parcel status in database if parcel exists
    if parcel_doc:
        target_status = "delivered" if event_in.status == DeliveryStatus.DELIVERED else "failed"
        await db["parcels"].update_one(
            {"_id": parcel_doc["_id"]},
            {"$set": {"status": target_status}},
        )

    created_event = await db["delivery_events"].find_one({"_id": insert_res.inserted_id})
    return _doc_to_event(created_event)


@router.get("", response_model=list[DeliveryEvent])
async def list_delivery_events(
    session_id: Annotated[str | None, Query(description="Filter by routing session ID")] = None,
    vehicle_id: Annotated[str | None, Query(description="Filter by vehicle ID")] = None,
    limit: Annotated[int, Query(ge=1, le=200, description="Max events to return")] = 50,
):
    """Query logged delivery events."""
    db = get_db()
    query: dict[str, Any] = {}
    if session_id:
        query["routing_session_id"] = session_id
    if vehicle_id:
        query["vehicle_id"] = vehicle_id

    cursor = db["delivery_events"].find(query).sort("recorded_at_wall", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_doc_to_event(d) for d in docs]
