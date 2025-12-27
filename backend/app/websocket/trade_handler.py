from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
import logging

from app.websocket.trade_manager import trade_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/trades/{season_id}")
async def trade_websocket(websocket: WebSocket, season_id: str):
    """WebSocket endpoint for real-time trade notifications."""
    logger.info(f"Trade WebSocket connection attempt for season: {season_id}")

    # Convert string to UUID
    try:
        season_uuid = UUID(season_id)
    except ValueError:
        logger.error(f"Invalid season_id format: {season_id}")
        await websocket.close(code=1008)
        return

    try:
        await trade_manager.connect(websocket, season_uuid)
        logger.info(f"Trade WebSocket connected for season: {season_id}")
    except Exception as e:
        logger.error(f"Failed to accept trade WebSocket connection: {e}")
        await websocket.close(code=1011)
        return

    try:
        while True:
            # Keep connection alive, receive any messages (ping/pong handled by FastAPI)
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"Trade WebSocket disconnected for season: {season_id}")
        await trade_manager.disconnect(websocket, season_uuid)
    except Exception as e:
        logger.error(f"Trade WebSocket error: {e}")
        await trade_manager.disconnect(websocket, season_uuid)
