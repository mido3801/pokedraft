from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
from typing import Optional
import json

from app.websocket.connection_manager import ConnectionManager
from app.websocket.draft_room import DraftRoom

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/draft/{draft_id}")
async def draft_websocket(websocket: WebSocket, draft_id: UUID):
    """
    WebSocket endpoint for live draft participation.

    Events from client:
    - join_draft: { user_token: str, display_name?: str }
    - make_pick: { pokemon_id: int }
    - place_bid: { pokemon_id: int, amount: int }  (auction only)
    - nominate: { pokemon_id: int }  (auction only)

    Events to client:
    - draft_state: Full current state on connection
    - pick_made: { team_id, pokemon_id, pick_number }
    - turn_start: { team_id, timer_end }
    - timer_tick: { seconds_remaining }
    - bid_update: { pokemon_id, bidder_id, amount }
    - draft_complete: { final_teams }
    - error: { message, code }
    - user_joined: { user_id, display_name }
    - user_left: { user_id }
    """
    await manager.connect(websocket, draft_id)

    try:
        # Send initial state
        room = await manager.get_or_create_room(draft_id)
        await websocket.send_json({
            "event": "draft_state",
            "data": room.get_state(),
        })

        while True:
            data = await websocket.receive_json()
            event = data.get("event")

            if event == "join_draft":
                await handle_join(websocket, draft_id, data.get("data", {}))
            elif event == "make_pick":
                await handle_pick(websocket, draft_id, data.get("data", {}))
            elif event == "place_bid":
                await handle_bid(websocket, draft_id, data.get("data", {}))
            elif event == "nominate":
                await handle_nominate(websocket, draft_id, data.get("data", {}))
            else:
                await websocket.send_json({
                    "event": "error",
                    "data": {"message": f"Unknown event: {event}", "code": "UNKNOWN_EVENT"},
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket, draft_id)
    except Exception as e:
        await websocket.send_json({
            "event": "error",
            "data": {"message": str(e), "code": "SERVER_ERROR"},
        })
        await manager.disconnect(websocket, draft_id)


async def handle_join(websocket: WebSocket, draft_id: UUID, data: dict):
    """Handle a user joining the draft."""
    user_token = data.get("user_token")
    display_name = data.get("display_name")

    room = await manager.get_or_create_room(draft_id)
    # TODO: Validate user and add to room

    await manager.broadcast(draft_id, {
        "event": "user_joined",
        "data": {"user_id": user_token, "display_name": display_name},
    })


async def handle_pick(websocket: WebSocket, draft_id: UUID, data: dict):
    """Handle a draft pick."""
    pokemon_id = data.get("pokemon_id")

    room = await manager.get_or_create_room(draft_id)
    # TODO: Validate it's the user's turn and Pokemon is available
    # TODO: Record pick and advance draft

    await manager.broadcast(draft_id, {
        "event": "pick_made",
        "data": {
            "team_id": "TODO",
            "pokemon_id": pokemon_id,
            "pick_number": room.current_pick,
        },
    })


async def handle_bid(websocket: WebSocket, draft_id: UUID, data: dict):
    """Handle an auction bid."""
    pokemon_id = data.get("pokemon_id")
    amount = data.get("amount")

    room = await manager.get_or_create_room(draft_id)
    # TODO: Validate bid is valid (higher than current, user has budget)

    await manager.broadcast(draft_id, {
        "event": "bid_update",
        "data": {
            "pokemon_id": pokemon_id,
            "bidder_id": "TODO",
            "amount": amount,
        },
    })


async def handle_nominate(websocket: WebSocket, draft_id: UUID, data: dict):
    """Handle an auction nomination."""
    pokemon_id = data.get("pokemon_id")

    room = await manager.get_or_create_room(draft_id)
    # TODO: Validate it's the user's turn to nominate

    await manager.broadcast(draft_id, {
        "event": "nomination",
        "data": {
            "pokemon_id": pokemon_id,
            "nominator_id": "TODO",
            "min_bid": 1,
        },
    })
