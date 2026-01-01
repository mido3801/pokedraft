from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
import logging

from app.websocket.waiver_manager import waiver_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/waivers/{season_id}")
async def waiver_websocket(websocket: WebSocket, season_id: str):
    """WebSocket endpoint for real-time waiver wire notifications."""
    logger.info(f"Waiver WebSocket connection attempt for season: {season_id}")

    # Convert string to UUID
    try:
        season_uuid = UUID(season_id)
    except ValueError:
        logger.error(f"Invalid season_id format: {season_id}")
        await websocket.close(code=1008)
        return

    try:
        await waiver_manager.connect(websocket, season_uuid)
        logger.info(f"Waiver WebSocket connected for season: {season_id}")
    except Exception as e:
        logger.error(f"Failed to accept waiver WebSocket connection: {e}")
        await websocket.close(code=1011)
        return

    try:
        while True:
            # Keep connection alive, receive any messages (ping/pong handled by FastAPI)
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"Waiver WebSocket disconnected for season: {season_id}")
        await waiver_manager.disconnect(websocket, season_uuid)
    except Exception as e:
        logger.error(f"Waiver WebSocket error: {e}")
        await waiver_manager.disconnect(websocket, season_uuid)
