"""
API Routers package — Phase 6.
"""

from app.routers.parcels import router as parcels_router
from app.routers.routing_sessions import router as routing_sessions_router
from app.routers.vehicles import router as vehicles_router
from app.routers.warehouses import router as warehouses_router

__all__ = [
    "parcels_router",
    "routing_sessions_router",
    "vehicles_router",
    "warehouses_router",
]
