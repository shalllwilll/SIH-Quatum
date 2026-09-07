"""
Models package for the backend application.

All time values are stored as int (minutes since midnight, 0–1439).
All distance values are stored as float (kilometres).
Never store display-formatted strings for times or distances — spec §3a rule.
"""

from app.models.delivery_event import DeliveryEvent, DeliveryEventCreate, DeliveryStatus
from app.models.parcel import Parcel, ParcelBase, ParcelCreate, ParcelStatus
from app.models.routing_session import (
    RoutingSession,
    RoutingSessionBase,
    RoutingSessionCreate,
    SessionPreset,
    SessionStatus,
)
from app.models.vehicle import (
    Vehicle,
    VehicleBase,
    VehicleCreate,
    VehicleStatus,
    VehicleUpdate,
)
from app.models.warehouse import Warehouse, WarehouseBase, WarehouseCreate

__all__ = [
    "DeliveryEvent",
    "DeliveryEventCreate",
    "DeliveryStatus",
    "Parcel",
    "ParcelBase",
    "ParcelCreate",
    "ParcelStatus",
    "RoutingSession",
    "RoutingSessionBase",
    "RoutingSessionCreate",
    "SessionPreset",
    "SessionStatus",
    "Vehicle",
    "VehicleBase",
    "VehicleCreate",
    "VehicleStatus",
    "VehicleUpdate",
    "Warehouse",
    "WarehouseBase",
    "WarehouseCreate",
]
