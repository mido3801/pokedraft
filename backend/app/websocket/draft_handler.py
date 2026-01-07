from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import logging
import asyncio

from sqlalchemy import select

from app.core.database import async_session_maker
from app.websocket.connection_manager import ConnectionManager
from app.websocket.draft_room import DraftRoom, DraftParticipant, DraftPick
from app.models.draft import Draft as DraftModel, DraftPick as DraftPickModel, DraftStatus
from app.models.team import Team as TeamModel
from app.models.season import Season as SeasonModel, SeasonStatus

logger = logging.getLogger(__name__)

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

        # Load auction-specific settings
        room.nomination_timer_seconds = draft.nomination_timer_seconds
        room.bid_timer_seconds = draft.bid_timer_seconds or 15
        room.min_bid = draft.min_bid or 1
        room.bid_increment = draft.bid_increment or 1

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
    """Mark draft as completed in database and update season status."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(DraftModel).where(DraftModel.id == draft_id)
        )
        draft = result.scalar_one_or_none()
        if draft:
            draft.status = DraftStatus.COMPLETED
            draft.completed_at = datetime.utcnow()

            # Update season status to active if this is a league draft
            if draft.season_id:
                season_result = await db.execute(
                    select(SeasonModel).where(SeasonModel.id == draft.season_id)
                )
                season = season_result.scalar_one_or_none()
                if season:
                    season.status = SeasonStatus.ACTIVE
                    season.started_at = datetime.utcnow()

            await db.commit()


async def start_draft_in_db(draft_id: UUID, pick_order: list[UUID]) -> bool:
    """Start the draft in database and update season status."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(DraftModel).where(DraftModel.id == draft_id)
        )
        draft = result.scalar_one_or_none()
        if draft and draft.status == DraftStatus.PENDING:
            draft.status = DraftStatus.LIVE
            draft.started_at = datetime.utcnow()
            draft.pick_order = [str(tid) for tid in pick_order]

            # Update season status to drafting if this is a league draft
            if draft.season_id:
                season_result = await db.execute(
                    select(SeasonModel).where(SeasonModel.id == draft.season_id)
                )
                season = season_result.scalar_one_or_none()
                if season:
                    season.status = SeasonStatus.DRAFTING

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

    # Verify auction format
    if room.format != "auction":
        await websocket.send_json({
            "event": "error",
            "data": {"message": "This is not an auction draft", "code": "NOT_AUCTION"},
        })
        return

    # Verify draft is live
    if room.status != "live":
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Draft is not live", "code": "DRAFT_NOT_LIVE"},
        })
        return

    # Verify we're in bidding phase
    if room.auction_phase != "bidding":
        await websocket.send_json({
            "event": "error",
            "data": {"message": "No active auction to bid on", "code": "NO_ACTIVE_AUCTION"},
        })
        return

    # Verify there's an active nomination
    if not room.current_nomination:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "No Pokemon is currently nominated", "code": "NO_NOMINATION"},
        })
        return

    # Verify bidding on the correct pokemon
    if room.current_nomination["pokemon_id"] != pokemon_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Invalid pokemon_id for current auction", "code": "WRONG_POKEMON"},
        })
        return

    team_id = websocket_to_team.get(websocket)
    if not team_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "You are not in this draft", "code": "NOT_IN_DRAFT"},
        })
        return

    # Verify not bidding against yourself
    if room.current_highest_bid and room.current_highest_bid["team_id"] == str(team_id):
        await websocket.send_json({
            "event": "error",
            "data": {"message": "You already have the highest bid", "code": "ALREADY_HIGHEST_BIDDER"},
        })
        return

    # Verify team has roster space
    if not room.has_roster_space(team_id):
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Your roster is full", "code": "ROSTER_FULL"},
        })
        return

    # Verify budget
    if not room.can_afford(team_id, amount):
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Cannot afford this bid", "code": "INSUFFICIENT_BUDGET"},
        })
        return

    # Verify bid meets minimum
    if amount < room.min_bid:
        await websocket.send_json({
            "event": "error",
            "data": {"message": f"Bid must be at least {room.min_bid}", "code": "BID_TOO_LOW"},
        })
        return

    # Verify bid increment
    current_bid = room.current_highest_bid["amount"] if room.current_highest_bid else 0
    min_required = current_bid + room.bid_increment
    if amount < min_required:
        await websocket.send_json({
            "event": "error",
            "data": {"message": f"Bid must be at least {min_required} (current: {current_bid} + increment: {room.bid_increment})", "code": "INSUFFICIENT_INCREMENT"},
        })
        return

    # Place the bid
    room.place_auction_bid(team_id, amount)

    # Reset bid timer
    room.timer_end = datetime.now(timezone.utc) + timedelta(seconds=room.bid_timer_seconds)

    # Cancel existing timer and start new one
    if room.bid_timer_task:
        room.bid_timer_task.cancel()

    room.bid_timer_task = asyncio.create_task(
        run_bid_timer(draft_id, room.bid_timer_seconds, pokemon_id)
    )

    # Broadcast bid update
    await manager.broadcast(draft_id, {
        "event": "bid_update",
        "data": {
            "pokemon_id": pokemon_id,
            "bidder_id": str(team_id),
            "bidder_name": room.participants[team_id].display_name,
            "amount": amount,
            "bid_timer_end": room.timer_end.isoformat(),
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

    # Verify auction format
    if room.format != "auction":
        await websocket.send_json({
            "event": "error",
            "data": {"message": "This is not an auction draft", "code": "NOT_AUCTION"},
        })
        return

    # Verify draft is live
    if room.status != "live":
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Draft is not live", "code": "DRAFT_NOT_LIVE"},
        })
        return

    team_id = websocket_to_team.get(websocket)
    if not team_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "You are not in this draft", "code": "NOT_IN_DRAFT"},
        })
        return

    # Verify no active nomination
    if room.current_nomination is not None:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "There is already an active nomination", "code": "NOMINATION_ACTIVE"},
        })
        return

    # Verify it's this team's turn to nominate
    nominating_team = room.get_nominating_team()
    if nominating_team != team_id:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "It's not your turn to nominate", "code": "NOT_YOUR_TURN"},
        })
        return

    # Verify pokemon is available
    if not room.is_pokemon_available(pokemon_id):
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Pokemon is not available", "code": "POKEMON_UNAVAILABLE"},
        })
        return

    # Verify nominator has roster space
    if not room.has_roster_space(team_id):
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Your roster is full", "code": "ROSTER_FULL"},
        })
        return

    # Verify nominator can afford min_bid (for auto-bid)
    if not room.can_afford(team_id, room.min_bid):
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Cannot afford minimum bid", "code": "INSUFFICIENT_BUDGET"},
        })
        return

    # Get pokemon data
    pokemon_data = next(
        (p for p in room.available_pokemon if p["pokemon_id"] == pokemon_id),
        {"name": "Unknown"}
    )
    pokemon_name = pokemon_data.get("name", "Unknown")

    # Start the nomination (auto-bids at min_bid)
    room.start_nomination(pokemon_id, pokemon_name, team_id)

    # Start bid timer
    room.timer_end = datetime.now(timezone.utc) + timedelta(seconds=room.bid_timer_seconds)

    # Cancel any existing timer task
    if room.bid_timer_task:
        room.bid_timer_task.cancel()

    # Create new timer task
    room.bid_timer_task = asyncio.create_task(
        run_bid_timer(draft_id, room.bid_timer_seconds, pokemon_id)
    )

    # Broadcast nomination event
    await manager.broadcast(draft_id, {
        "event": "nomination",
        "data": {
            "pokemon_id": pokemon_id,
            "pokemon_name": pokemon_name,
            "nominator_id": str(team_id),
            "nominator_name": room.participants[team_id].display_name,
            "min_bid": room.min_bid,
            "current_bid": room.min_bid,
            "current_bidder_id": str(team_id),
            "current_bidder_name": room.participants[team_id].display_name,
            "bid_timer_end": room.timer_end.isoformat(),
        },
    })


async def run_bid_timer(draft_id: UUID, seconds: int, pokemon_id: int):
    """Run the bid timer and complete auction when it expires."""
    try:
        await asyncio.sleep(seconds)
        await complete_auction(draft_id, pokemon_id)
    except asyncio.CancelledError:
        # Timer was cancelled (new bid placed), this is expected
        pass


async def complete_auction(draft_id: UUID, pokemon_id: int):
    """Complete an auction and award the pokemon to the highest bidder."""
    room = await manager.get_or_create_room(draft_id)

    # Verify auction is still active for this pokemon
    if not room.current_nomination or room.current_nomination["pokemon_id"] != pokemon_id:
        return

    if not room.current_highest_bid:
        # No bids - shouldn't happen since nominator auto-bids
        room.clear_auction_state()
        return

    # Get winning team info
    winner_team_id = UUID(room.current_highest_bid["team_id"])
    winner_team_name = room.current_highest_bid["team_name"]
    winning_amount = room.current_highest_bid["amount"]
    pokemon_name = room.current_nomination["pokemon_name"]

    # Make the pick (this handles budget deduction and roster addition)
    try:
        pick = room.make_pick(winner_team_id, pokemon_id, winning_amount)

        # Get full pokemon data for removal from available
        room.available_pokemon = [
            p for p in room.available_pokemon if p["pokemon_id"] != pokemon_id
        ]

        # Save to database
        await save_pick_to_db(draft_id, winner_team_id, pokemon_id, pick.pick_number, winning_amount)

        # Broadcast pick made
        await manager.broadcast(draft_id, {
            "event": "pick_made",
            "data": {
                "team_id": str(winner_team_id),
                "team_name": winner_team_name,
                "pokemon_id": pokemon_id,
                "pokemon_name": pokemon_name,
                "pick_number": pick.pick_number,
                "points_spent": winning_amount,
            },
        })

        # Clear auction state
        room.clear_auction_state()

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
                            "budget_remaining": p.budget_remaining,
                        }
                        for p in room.participants.values()
                    ],
                },
            })
        else:
            # Advance to next nominator
            room.advance_nominating_team()
            next_team = room.get_nominating_team()

            if next_team:
                # Broadcast turn start for next nominator
                await manager.broadcast(draft_id, {
                    "event": "turn_start",
                    "data": {
                        "team_id": str(next_team),
                        "team_name": room.participants[next_team].display_name,
                        "phase": "nominating",
                    },
                })

    except ValueError as e:
        # Pick failed for some reason - log and notify
        logger.error(f"Auction completion failed for draft {draft_id}: {e}")
        room.clear_auction_state()
        await manager.broadcast(draft_id, {
            "event": "error",
            "data": {"message": f"Auction failed: {str(e)}", "code": "AUCTION_ERROR"},
        })
