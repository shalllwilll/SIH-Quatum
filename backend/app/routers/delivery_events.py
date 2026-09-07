"""
backend/app/routers/delivery_events.py — Milestone 6.3

Endpoints for logging and querying delivery outcomes (delivered / failed):
- POST /delivery-events (record delivery attempt, update parcel status)
- GET /delivery-events (list logged delivery events)
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

router = APIRouter(prefix="/delivery-events", tags=["Delivery Events"])


class DeliveryEventCreateRequest(BaseModel):
    """Payload to log a delivery outcome."""

    routing_session_id: str = Field(..., description="ID of the active RoutingSession")
    vehicle_id: str = Field(..., description="ID or label of the delivering vehicle")
    parcel_id: str = Field(..., description="ID or tracking number of the parcel")
    status: DeliveryStatus = Field(..., description="Delivery result: delivered or failed")
    recorded_at_min: int = Field(..., ge=0, le=1439, description="Simulated minutes since midnight")
    note: str | None = Field(None, description="Optional driver note or failure reason")


def _doc_to_event(doc: dict[str, Any]) -> DeliveryEvent:
    """Convert MongoDB document to Pydantic DeliveryEvent model."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return DeliveryEvent.model_validate(doc)


@router.post("", response_model=DeliveryEvent, status_code=status.HTTP_201_CREATED)
async def create_delivery_event(event_in: DeliveryEventCreateRequest):
    """Record a delivery event and update parcel status."""
    db = get_db()

    # Validate parcel exists in database
    parcel_doc = None
    try:
        parcel_doc = await db["parcels"].find_one({"_id": ObjectId(event_in.parcel_id)})
    except (InvalidId, Exception):
        # Also try matching on tracking string or address if ObjectId invalid
        parcel_doc = await db["parcels"].find_one({"parcel_id": event_in.parcel_id})

    if not parcel_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with ID '{event_in.parcel_id}' not found.",
        )

    # Prepare event document
    event_doc = {
        "routing_session_id": event_in.routing_session_id,
        "vehicle_id": event_in.vehicle_id,
        "parcel_id": event_in.parcel_id,
        "status": event_in.status.value,
        "recorded_at_min": event_in.recorded_at_min,
        "recorded_at_wall": time.time(),
        "note": event_in.note,
    }

    insert_res = await db["delivery_events"].insert_one(event_doc)

    # Update parcel status
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
