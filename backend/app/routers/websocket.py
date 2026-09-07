"""
backend/app/routers/websocket.py — Real-Time Telemetry Streaming over WebSockets

Provides low-latency bi-directional WebSocket channels:
- /ws/fleet: Broadcasts real-time vehicle positions, status updates, and dispatch events to Admin portals.
- /ws/driver/{driver_id}: Streams dedicated route assignments and telemetry updates to Driver portals.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

log = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    """Manages active WebSocket connections for fleet dispatchers and drivers."""

    def __init__(self):
        self.fleet_connections: list[WebSocket] = []
        self.driver_connections: dict[str, list[WebSocket]] = {}

    async def connect_fleet(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.fleet_connections.append(websocket)
        log.info("Fleet dispatcher WebSocket connected. Total active: %d", len(self.fleet_connections))

    def disconnect_fleet(self, websocket: WebSocket) -> None:
        if websocket in self.fleet_connections:
            self.fleet_connections.remove(websocket)
            log.info("Fleet dispatcher WebSocket disconnected. Total active: %d", len(self.fleet_connections))

    async def connect_driver(self, driver_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if driver_id not in self.driver_connections:
            self.driver_connections[driver_id] = []
        self.driver_connections[driver_id].append(websocket)
        log.info("Driver [%s] WebSocket connected. Total active for driver: %d", driver_id, len(self.driver_connections[driver_id]))

    def disconnect_driver(self, driver_id: str, websocket: WebSocket) -> None:
        if driver_id in self.driver_connections and websocket in self.driver_connections[driver_id]:
            self.driver_connections[driver_id].remove(websocket)
            if not self.driver_connections[driver_id]:
                del self.driver_connections[driver_id]
            log.info("Driver [%s] WebSocket disconnected.", driver_id)

    async def broadcast_fleet(self, message: dict[str, Any]) -> None:
        """Broadcast telemetry or status payload to all connected fleet dispatcher clients."""
        payload_str = json.dumps(message)
        dead_connections = []
        for connection in self.fleet_connections:
            try:
                await connection.send_text(payload_str)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect_fleet(dead)

    async def send_to_driver(self, driver_id: str, message: dict[str, Any]) -> None:
        """Send message payload to a specific driver's active WebSocket clients."""
        if driver_id not in self.driver_connections:
            return

        payload_str = json.dumps(message)
        dead_connections = []
        for connection in self.driver_connections[driver_id]:
            try:
                await connection.send_text(payload_str)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect_driver(driver_id, dead)


# Singleton connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/fleet")
async def websocket_fleet_endpoint(websocket: WebSocket):
    """WebSocket stream for real-time fleet positions and status changes."""
    await manager.connect_fleet(websocket)
    try:
        while True:
            # Keep-alive receive loop
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect_fleet(websocket)
    except Exception as exc:
        log.debug("Fleet WebSocket closed with exception: %s", exc)
        manager.disconnect_fleet(websocket)


@router.websocket("/ws/driver/{driver_id}")
async def websocket_driver_endpoint(websocket: WebSocket, driver_id: str):
    """WebSocket stream for driver manifest updates and position telemetry."""
    await manager.connect_driver(driver_id, websocket)
    try:
        while True:
            # Keep-alive receive loop
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect_driver(driver_id, websocket)
    except Exception as exc:
        log.debug("Driver [%s] WebSocket closed with exception: %s", driver_id, exc)
        manager.disconnect_driver(driver_id, websocket)
