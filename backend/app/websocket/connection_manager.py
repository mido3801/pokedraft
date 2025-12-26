from fastapi import WebSocket
from uuid import UUID
from typing import Dict, List, Set
import asyncio

from app.websocket.draft_room import DraftRoom


class ConnectionManager:
    """
    Manages WebSocket connections for draft rooms.

    Each draft has its own room with connected users.
    """

    def __init__(self):
        # Map of draft_id -> set of connected websockets
        self.connections: Dict[UUID, Set[WebSocket]] = {}
        # Map of draft_id -> DraftRoom instance
        self.rooms: Dict[UUID, DraftRoom] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, draft_id: UUID):
        """Accept a new WebSocket connection and add to draft room."""
        await websocket.accept()

        async with self._lock:
            if draft_id not in self.connections:
                self.connections[draft_id] = set()
            self.connections[draft_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, draft_id: UUID):
        """Remove a WebSocket connection from draft room."""
        async with self._lock:
            if draft_id in self.connections:
                self.connections[draft_id].discard(websocket)
                # Clean up empty rooms
                if not self.connections[draft_id]:
                    del self.connections[draft_id]
                    if draft_id in self.rooms:
                        del self.rooms[draft_id]

    async def broadcast(self, draft_id: UUID, message: dict):
        """Send a message to all connections in a draft room."""
        if draft_id not in self.connections:
            return

        # Copy the set to avoid modification during iteration
        async with self._lock:
            connections = set(self.connections.get(draft_id, set()))

        dead_connections = set()
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.add(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            await self.disconnect(websocket, draft_id)

    async def send_to_user(self, draft_id: UUID, user_id: str, message: dict):
        """Send a message to a specific user in a draft room."""
        # TODO: Implement user-specific messaging
        # This requires tracking which websocket belongs to which user
        pass

    async def get_or_create_room(self, draft_id: UUID) -> DraftRoom:
        """Get or create a DraftRoom for the given draft."""
        async with self._lock:
            if draft_id not in self.rooms:
                room = DraftRoom(draft_id)
                room.is_loading = True
                self.rooms[draft_id] = room
            return self.rooms[draft_id]

    async def mark_room_loaded(self, draft_id: UUID):
        """Mark a room as fully loaded."""
        async with self._lock:
            if draft_id in self.rooms:
                self.rooms[draft_id].is_loading = False

    def get_connection_count(self, draft_id: UUID) -> int:
        """Get the number of connections in a draft room."""
        return len(self.connections.get(draft_id, set()))
