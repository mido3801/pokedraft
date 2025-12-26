from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict

from sqlalchemy import select

from app.core.database import async_session_maker
from app.websocket.connection_manager import ConnectionManager
from app.websocket.draft_room import DraftRoom, DraftParticipant, DraftPick
from app.models.draft import Draft as DraftModel, DraftPick as DraftPickModel, DraftStatus
from app.models.team import Team as TeamModel

router = APIRouter()
manager = ConnectionManager()

# Track websocket to team mapping
websocket_to_team: Dict[WebSocket, UUID] = {}


async def load_draft_state(draft_id: UUID, room: DraftRoom):
    """Load draft state from database into room."""
    async with async_session_maker() as db:
        # Get draft
        result = await db.execute(
            select(DraftModel).where(DraftModel.id == draft_id)
        )
        draft = result.scalar_one_or_none()

        if not draft:
            return False

        room.status = draft.status.value
        room.format = draft.format.value
        room.roster_size = draft.roster_size
        room.timer_seconds = draft.timer_seconds
        room.budget_enabled = draft.budget_enabled
        room.budget_per_team = draft.budget_per_team
        room.current_pick = draft.current_pick
        room.rejoin_code = draft.rejoin_code

        # Load pokemon pool
        room.available_pokemon = []
        for pid_str, data in draft.pokemon_pool.items():
            room.available_pokemon.append({
                "pokemon_id": int(pid_str),
                "name": data.get("name", ""),
                "points": data.get("points"),
                "types": data.get("types", []),
                "stats": data.get("stats"),
                "generation": data.get("generation"),
                "is_legendary": data.get("is_legendary", False),
                "is_mythical": data.get("is_mythical", False),
                "abilities": data.get("abilities", []),
            })

        # Load teams
        teams_result = await db.execute(
            select(TeamModel)
            .where(TeamModel.draft_id == draft_id)
            .order_by(TeamModel.draft_position)
        )
        teams = teams_result.scalars().all()

        room.pick_order = []
        for team in teams:
            room.pick_order.append(team.id)
            room.participants[team.id] = DraftParticipant(
                team_id=team.id,
                user_id=team.user_id,
                display_name=team.display_name,
                session_token=team.session_token,
                draft_position=team.draft_position or 0,
                budget_remaining=team.budget_remaining,
                pokemon=[],
            )

        # Load picks
        picks_result = await db.execute(
            select(DraftPickModel)
            .where(DraftPickModel.draft_id == draft_id)
            .order_by(DraftPickModel.pick_number)
        )
        picks = picks_result.scalars().all()

        room.picks = []
        picked_ids = set()
        for pick in picks:
            room.picks.append(DraftPick(
                pick_number=pick.pick_number,
                team_id=pick.team_id,
                pokemon_id=pick.pokemon_id,
                points_spent=pick.points_spent,
                picked_at=pick.picked_at,
            ))
            picked_ids.add(pick.pokemon_id)

            # Add to team's pokemon list
            if pick.team_id in room.participants:
                room.participants[pick.team_id].pokemon.append(pick.pokemon_id)

        # Remove picked pokemon from available
        room.available_pokemon = [
            p for p in room.available_pokemon if p["pokemon_id"] not in picked_ids
        ]

        return True


async def save_pick_to_db(draft_id: UUID, team_id: UUID, pokemon_id: int, pick_number: int, points_spent: Optional[int] = None):
    """Save a pick to the database."""
    async with async_session_maker() as db:
        # Create pick record
        pick = DraftPickModel(
            draft_id=draft_id,
            team_id=team_id,
            pokemon_id=pokemon_id,
            pick_number=pick_number,
            points_spent=points_spent,
        )
        db.add(pick)

        # Update draft current_pick
        draft_result = await db.execute(
            select(DraftModel).where(DraftModel.id == draft_id)
        )
        draft = draft_result.scalar_one_or_none()
        if draft:
            draft.current_pick = pick_number + 1

        # Update team budget if applicable
        if points_spent:
            team_result = await db.execute(
                select(TeamModel).where(TeamModel.id == team_id)
            )
            team = team_result.scalar_one_or_none()
            if team and team.budget_remaining:
                team.budget_remaining -= points_spent

        await db.commit()


async def complete_draft_in_db(draft_id: UUID):
    """Mark draft as completed in database."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(DraftModel).where(DraftModel.id == draft_id)
        )
        draft = result.scalar_one_or_none()
        if draft:
            draft.status = DraftStatus.COMPLETED
            draft.completed_at = datetime.utcnow()
            await db.commit()


async def start_draft_in_db(draft_id: UUID, pick_order: list[UUID]) -> bool:
    """Start the draft in database."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(DraftModel).where(DraftModel.id == draft_id)
        )
        draft = result.scalar_one_or_none()
        if draft and draft.status == DraftStatus.PENDING:
            draft.status = DraftStatus.LIVE
            draft.started_at = datetime.utcnow()
            draft.pick_order = [str(tid) for tid in pick_order]
            await db.commit()
            return True
        return False


@router.websocket("/ws/draft/{draft_id}")
async def draft_websocket(websocket: WebSocket, draft_id: UUID):
    """
    WebSocket endpoint for live draft participation.

    Events from client:
    - join_draft: { user_token: str, team_id?: str }
    - make_pick: { pokemon_id: int, points?: int }
    - place_bid: { pokemon_id: int, amount: int }  (auction only)
    - nominate: { pokemon_id: int }  (auction only)

    Events to client:
    - draft_state: Full current state on connection
    - pick_made: { team_id, pokemon_id, pick_number, pokemon_name }
    - turn_start: { team_id, timer_end }
    - draft_complete: { final_teams }
    - error: { message, code }
    - user_joined: { team_id, display_name }
    - user_left: { team_id }
    """
    await manager.connect(websocket, draft_id)

    try:
        # Load state from database (only first connection loads)
        room = await manager.get_or_create_room(draft_id)

        # Use a lock to ensure only one connection loads the draft state
        if room.is_loading:
            async with room.load_lock:
                # Double-check after acquiring lock (another connection may have loaded it)
                if room.is_loading:
                    await load_draft_state(draft_id, room)
                    room.is_loading = False

        # Send initial state
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
            elif event == "start_draft":
                await handle_start_draft(websocket, draft_id, data.get("data", {}))
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
        team_id = websocket_to_team.pop(websocket, None)
        if team_id:
            room = await manager.get_or_create_room(draft_id)
            participant = room.participants.get(team_id)
            await manager.broadcast(draft_id, {
                "event": "user_left",
                "data": {
                    "team_id": str(team_id),
                    "display_name": participant.display_name if participant else "Unknown",
                },
            })
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
    team_id_str = data.get("team_id")

    room = await manager.get_or_create_room(draft_id)

    # Find the team by session token or team_id
    matched_team = None
    if team_id_str:
        try:
            team_id = UUID(team_id_str)
            matched_team = room.participants.get(team_id)
        except ValueError:
            pass

    if not matched_team and user_token:
        for participant in room.participants.values():
            if participant.session_token == user_token:
                matched_team = participant
                break

    # If team not found in cached room, check database for newly joined teams
    if not matched_team and (team_id_str or user_token):
        async with async_session_maker() as db:
            team = None

            # Try to find by team_id first
            if team_id_str:
                try:
                    team_id = UUID(team_id_str)
                    result = await db.execute(
                        select(TeamModel)
                        .where(TeamModel.draft_id == draft_id)
                        .where(TeamModel.id == team_id)
                    )
                    team = result.scalar_one_or_none()
                except ValueError:
                    pass

            # If not found by team_id, try session_token
            if not team and user_token:
                result = await db.execute(
                    select(TeamModel)
                    .where(TeamModel.draft_id == draft_id)
                    .where(TeamModel.session_token == user_token)
                )
                team = result.scalar_one_or_none()

            if team:
                # Add newly found team to room participants
                room.participants[team.id] = DraftParticipant(
                    team_id=team.id,
                    user_id=team.user_id,
                    display_name=team.display_name,
                    session_token=team.session_token,
                    draft_position=team.draft_position or 0,
                    budget_remaining=team.budget_remaining,
                    pokemon=[],
                )
                # Update pick order if not already present
                if team.id not in room.pick_order:
                    room.pick_order.append(team.id)
                matched_team = room.participants[team.id]

    if matched_team:
        websocket_to_team[websocket] = matched_team.team_id
        await manager.broadcast(draft_id, {
            "event": "user_joined",
            "data": {
                "team_id": str(matched_team.team_id),
                "display_name": matched_team.display_name,
            },
        })
    else:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Team not found", "code": "TEAM_NOT_FOUND"},
        })


async def handle_start_draft(websocket: WebSocket, draft_id: UUID, data: dict):
    """Handle starting the draft."""
    room = await manager.get_or_create_room(draft_id)

    # Verify draft is pending
    if room.status != "pending":
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Draft is not in pending state", "code": "DRAFT_NOT_PENDING"},
        })
        return

    # Verify the sender is in the draft
    team_id = websocket_to_team.get(websocket)
    if not team_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "You are not in this draft", "code": "NOT_IN_DRAFT"},
        })
        return

    # Verify sender is the draft creator (draft_position == 0)
    participant = room.participants.get(team_id)
    if not participant or participant.draft_position != 0:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Only the draft creator can start the draft", "code": "NOT_CREATOR"},
        })
        return

    # Verify at least 2 teams
    if len(room.participants) < 2:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Need at least 2 teams to start", "code": "NOT_ENOUGH_TEAMS"},
        })
        return

    # Start the draft
    room.status = "live"
    room.pick_order = sorted(room.pick_order, key=lambda tid: room.participants[tid].draft_position)

    # Set timer if applicable
    if room.timer_seconds:
        room.timer_end = datetime.now(timezone.utc).replace(microsecond=0) + \
            timedelta(seconds=room.timer_seconds)

    # Save to database
    await start_draft_in_db(draft_id, room.pick_order)

    # Broadcast draft started to all clients
    first_team = room.get_current_team()
    await manager.broadcast(draft_id, {
        "event": "draft_started",
        "data": {
            "status": "live",
            "pick_order": [str(tid) for tid in room.pick_order],
            "current_team_id": str(first_team) if first_team else None,
            "current_team_name": room.participants[first_team].display_name if first_team else None,
            "timer_end": room.timer_end.isoformat() if room.timer_end else None,
        },
    })


async def handle_pick(websocket: WebSocket, draft_id: UUID, data: dict):
    """Handle a draft pick."""
    pokemon_id = data.get("pokemon_id")
    points = data.get("points")

    if not pokemon_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "pokemon_id is required", "code": "MISSING_POKEMON_ID"},
        })
        return

    room = await manager.get_or_create_room(draft_id)

    # Verify draft is live
    if room.status != "live":
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Draft is not live", "code": "DRAFT_NOT_LIVE"},
        })
        return

    # Get the team making the pick
    team_id = websocket_to_team.get(websocket)
    if not team_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "You are not in this draft", "code": "NOT_IN_DRAFT"},
        })
        return

    # Verify it's this team's turn
    current_team = room.get_current_team()
    if current_team != team_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "It's not your turn", "code": "NOT_YOUR_TURN"},
        })
        return

    # Verify pokemon is available
    if not room.is_pokemon_available(pokemon_id):
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Pokemon is not available", "code": "POKEMON_UNAVAILABLE"},
        })
        return

    # Verify budget if applicable
    if room.budget_enabled and points is not None:
        if not room.can_afford(team_id, points):
            await websocket.send_json({
                "event": "error",
                "data": {"message": "Cannot afford this Pokemon", "code": "INSUFFICIENT_BUDGET"},
            })
            return

    # Make the pick
    try:
        pick = room.make_pick(team_id, pokemon_id, points)

        # Get pokemon name
        pokemon_data = next(
            (p for p in room.available_pokemon if p["pokemon_id"] == pokemon_id),
            {"name": "Unknown"}
        )

        # Remove from available
        room.available_pokemon = [
            p for p in room.available_pokemon if p["pokemon_id"] != pokemon_id
        ]

        # Save to database
        await save_pick_to_db(draft_id, team_id, pokemon_id, pick.pick_number, points)

        # Broadcast pick
        await manager.broadcast(draft_id, {
            "event": "pick_made",
            "data": {
                "team_id": str(team_id),
                "team_name": room.participants[team_id].display_name,
                "pokemon_id": pokemon_id,
                "pokemon_name": pokemon_data.get("name", "Unknown"),
                "pick_number": pick.pick_number,
                "points_spent": points,
            },
        })

        # Check if draft is complete
        if room.status == "completed":
            await complete_draft_in_db(draft_id)
            await manager.broadcast(draft_id, {
                "event": "draft_complete",
                "data": {
                    "teams": [
                        {
                            "team_id": str(p.team_id),
                            "display_name": p.display_name,
                            "pokemon": p.pokemon,
                        }
                        for p in room.participants.values()
                    ],
                },
            })
        else:
            # Notify next team
            next_team = room.get_current_team()
            if next_team:
                await manager.broadcast(draft_id, {
                    "event": "turn_start",
                    "data": {
                        "team_id": str(next_team),
                        "team_name": room.participants[next_team].display_name,
                        "timer_end": room.timer_end.isoformat() if room.timer_end else None,
                    },
                })

    except ValueError as e:
        await websocket.send_json({
            "event": "error",
            "data": {"message": str(e), "code": "PICK_ERROR"},
        })


async def handle_bid(websocket: WebSocket, draft_id: UUID, data: dict):
    """Handle an auction bid."""
    pokemon_id = data.get("pokemon_id")
    amount = data.get("amount")

    if not pokemon_id or amount is None:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "pokemon_id and amount are required", "code": "MISSING_PARAMS"},
        })
        return

    room = await manager.get_or_create_room(draft_id)

    if room.format != "auction":
        await websocket.send_json({
            "event": "error",
            "data": {"message": "This is not an auction draft", "code": "NOT_AUCTION"},
        })
        return

    team_id = websocket_to_team.get(websocket)
    if not team_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "You are not in this draft", "code": "NOT_IN_DRAFT"},
        })
        return

    # Verify budget
    if not room.can_afford(team_id, amount):
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Cannot afford this bid", "code": "INSUFFICIENT_BUDGET"},
        })
        return

    # Track current bid (simplified - would need more state for full auction)
    await manager.broadcast(draft_id, {
        "event": "bid_update",
        "data": {
            "pokemon_id": pokemon_id,
            "bidder_id": str(team_id),
            "bidder_name": room.participants[team_id].display_name,
            "amount": amount,
        },
    })


async def handle_nominate(websocket: WebSocket, draft_id: UUID, data: dict):
    """Handle an auction nomination."""
    pokemon_id = data.get("pokemon_id")

    if not pokemon_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "pokemon_id is required", "code": "MISSING_POKEMON_ID"},
        })
        return

    room = await manager.get_or_create_room(draft_id)

    if room.format != "auction":
        await websocket.send_json({
            "event": "error",
            "data": {"message": "This is not an auction draft", "code": "NOT_AUCTION"},
        })
        return

    team_id = websocket_to_team.get(websocket)
    if not team_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "You are not in this draft", "code": "NOT_IN_DRAFT"},
        })
        return

    # Verify pokemon is available
    if not room.is_pokemon_available(pokemon_id):
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Pokemon is not available", "code": "POKEMON_UNAVAILABLE"},
        })
        return

    pokemon_data = next(
        (p for p in room.available_pokemon if p["pokemon_id"] == pokemon_id),
        {"name": "Unknown"}
    )

    await manager.broadcast(draft_id, {
        "event": "nomination",
        "data": {
            "pokemon_id": pokemon_id,
            "pokemon_name": pokemon_data.get("name", "Unknown"),
            "nominator_id": str(team_id),
            "nominator_name": room.participants[team_id].display_name,
            "min_bid": 1,
        },
    })
