"""
API Routers package — Phase 6 & Phase 10.
"""

from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.delivery_events import router as delivery_events_router
from app.routers.driver import router as driver_router
from app.routers.parcels import router as parcels_router
from app.routers.routing_sessions import router as routing_sessions_router
from app.routers.traffic import router as traffic_router
from app.routers.vehicles import router as vehicles_router
from app.routers.warehouses import router as warehouses_router
from app.routers.websocket import router as websocket_router

__all__ = [
    "analytics_router",
    "auth_router",
    "delivery_events_router",
    "driver_router",
    "parcels_router",
    "routing_sessions_router",
    "traffic_router",
    "vehicles_router",
    "warehouses_router",
    "websocket_router",
]
