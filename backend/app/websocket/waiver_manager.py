from fastapi import WebSocket
from uuid import UUID
from typing import Dict, Set
import asyncio


class WaiverConnectionManager:
    """
    Manages WebSocket connections for waiver wire notifications per season.

    Similar to TradeConnectionManager - broadcasts waiver events to all
    connected clients in a season.
    """

    def __init__(self):
        # Map of season_id -> set of connected websockets
        self.connections: Dict[UUID, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, season_id: UUID):
        """Accept a new WebSocket connection for a season."""
        await websocket.accept()

        async with self._lock:
            if season_id not in self.connections:
                self.connections[season_id] = set()
            self.connections[season_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, season_id: UUID):
        """Remove a WebSocket connection."""
        async with self._lock:
            if season_id in self.connections:
                self.connections[season_id].discard(websocket)
                if not self.connections[season_id]:
                    del self.connections[season_id]

    async def broadcast(self, season_id: UUID, message: dict):
        """Send a message to all connections in a season."""
        if season_id not in self.connections:
            return

        async with self._lock:
            connections = set(self.connections.get(season_id, set()))

        dead_connections = set()
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.add(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            await self.disconnect(websocket, season_id)


# Global instance
waiver_manager = WaiverConnectionManager()
