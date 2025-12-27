from fastapi import APIRouter, Depends, status, Query
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.errors import (
    season_not_found,
    trade_not_found,
    team_not_found,
    not_league_owner,
    bad_request,
    forbidden,
)
from app.core.auth import get_season as fetch_season
from app.schemas.trade import Trade, TradeCreate
from app.models.trade import Trade as TradeModel, TradeStatus
from app.models.team import Team as TeamModel
from app.models.draft import DraftPick
from app.models.season import Season as SeasonModel, SeasonStatus
from app.models.league import League as LeagueModel
from app.models.user import User
from app.services.response_builders import build_trade_response
from app.websocket.trade_manager import trade_manager

router = APIRouter()


@router.post("", response_model=Trade, status_code=status.HTTP_201_CREATED)
async def propose_trade(
    trade: TradeCreate,
    season_id: UUID = Query(..., description="Season for the trade"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Propose a trade to another team."""
    season = await fetch_season(season_id, db)

    if season.status != SeasonStatus.ACTIVE:
        raise bad_request("Trades can only occur during an active season")

    # Get league settings
    league_result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = league_result.scalar_one_or_none()

    # Get proposer's team
    proposer_result = await db.execute(
        select(TeamModel)
        .where(TeamModel.season_id == season_id)
        .where(TeamModel.user_id == current_user.id)
    )
    proposer_team = proposer_result.scalar_one_or_none()

    if not proposer_team:
        raise forbidden("You don't have a team in this season")

    # Verify recipient team exists
    recipient_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.recipient_team_id)
    )
    recipient_team = recipient_result.scalar_one_or_none()

    if not recipient_team or recipient_team.season_id != season_id:
        raise team_not_found(trade.recipient_team_id)

    if recipient_team.id == proposer_team.id:
        raise bad_request("Cannot trade with yourself")

    # Verify proposer owns the pokemon they're offering (using DraftPick records)
    for pokemon_id in trade.proposer_pokemon:
        pokemon_result = await db.execute(
            select(DraftPick)
            .where(DraftPick.id == pokemon_id)
            .where(DraftPick.team_id == proposer_team.id)
        )
        if not pokemon_result.scalar_one_or_none():
            raise bad_request(f"You don't own pokemon {pokemon_id}")

    # Verify recipient owns the pokemon being requested
    for pokemon_id in trade.recipient_pokemon:
        pokemon_result = await db.execute(
            select(DraftPick)
            .where(DraftPick.id == pokemon_id)
            .where(DraftPick.team_id == recipient_team.id)
        )
        if not pokemon_result.scalar_one_or_none():
            raise bad_request(f"Recipient doesn't own pokemon {pokemon_id}")

    # Check if trade requires approval
    requires_approval = league.settings.get("trade_approval_required", False) if league else False

    db_trade = TradeModel(
        season_id=season_id,
        proposer_team_id=proposer_team.id,
        recipient_team_id=trade.recipient_team_id,
        proposer_pokemon=trade.proposer_pokemon,
        recipient_pokemon=trade.recipient_pokemon,
        message=trade.message,
        requires_approval=requires_approval,
    )
    db.add(db_trade)
    await db.commit()
    await db.refresh(db_trade)

    response = await build_trade_response(db_trade, db)

    # Broadcast trade proposal
    await trade_manager.broadcast(season_id, {
        "event": "trade_proposed",
        "data": {"trade": response}
    })

    return response


@router.get("", response_model=list[Trade])
async def list_trades(
    season_id: UUID = Query(..., description="Season to list trades for"),
    status_filter: str = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List trades in a season."""
    query = select(TradeModel).where(TradeModel.season_id == season_id)

    if status_filter:
        try:
            trade_status = TradeStatus(status_filter)
            query = query.where(TradeModel.status == trade_status)
        except ValueError:
            raise bad_request(f"Invalid status: {status_filter}")

    result = await db.execute(query.order_by(TradeModel.created_at.desc()))
    trades = result.scalars().all()

    return [await build_trade_response(trade, db) for trade in trades]


@router.get("/{trade_id}", response_model=Trade)
async def get_trade(
    trade_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get trade details."""
    result = await db.execute(
        select(TradeModel).where(TradeModel.id == trade_id)
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise trade_not_found(trade_id)

    return await build_trade_response(trade, db)


@router.post("/{trade_id}/accept", response_model=Trade)
async def accept_trade(
    trade_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept a trade proposal."""
    result = await db.execute(
        select(TradeModel).where(TradeModel.id == trade_id)
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise trade_not_found(trade_id)

    if trade.status != TradeStatus.PENDING:
        raise bad_request("Trade is not pending")

    # Verify user owns the recipient team
    recipient_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.recipient_team_id)
    )
    recipient_team = recipient_result.scalar_one_or_none()

    if not recipient_team or recipient_team.user_id != current_user.id:
        raise forbidden("Only the recipient can accept this trade")

    # If requires approval, set to accepted but wait for admin
    if trade.requires_approval:
        trade.status = TradeStatus.ACCEPTED
        await db.commit()
        await db.refresh(trade)
        response = await build_trade_response(trade, db)

        # Broadcast acceptance (awaiting admin approval)
        await trade_manager.broadcast(trade.season_id, {
            "event": "trade_accepted",
            "data": {"trade_id": str(trade.id), "requires_approval": True}
        })

        return response

    # Execute the trade
    await execute_trade(trade, db)
    trade.status = TradeStatus.ACCEPTED
    trade.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(trade)

    response = await build_trade_response(trade, db)

    # Broadcast acceptance (trade executed)
    await trade_manager.broadcast(trade.season_id, {
        "event": "trade_accepted",
        "data": {"trade_id": str(trade.id), "requires_approval": False, "trade": response}
    })

    return response


@router.post("/{trade_id}/reject", response_model=Trade)
async def reject_trade(
    trade_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a trade proposal."""
    result = await db.execute(
        select(TradeModel).where(TradeModel.id == trade_id)
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise trade_not_found(trade_id)

    if trade.status != TradeStatus.PENDING:
        raise bad_request("Trade is not pending")

    # Verify user owns the recipient team
    recipient_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.recipient_team_id)
    )
    recipient_team = recipient_result.scalar_one_or_none()

    if not recipient_team or recipient_team.user_id != current_user.id:
        raise forbidden("Only the recipient can reject this trade")

    trade.status = TradeStatus.REJECTED
    trade.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(trade)

    response = await build_trade_response(trade, db)

    # Broadcast rejection
    await trade_manager.broadcast(trade.season_id, {
        "event": "trade_rejected",
        "data": {"trade_id": str(trade.id)}
    })

    return response


@router.post("/{trade_id}/cancel", response_model=Trade)
async def cancel_trade(
    trade_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a trade proposal (proposer only)."""
    result = await db.execute(
        select(TradeModel).where(TradeModel.id == trade_id)
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise trade_not_found(trade_id)

    if trade.status != TradeStatus.PENDING:
        raise bad_request("Trade is not pending")

    # Verify user owns the proposer team
    proposer_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.proposer_team_id)
    )
    proposer_team = proposer_result.scalar_one_or_none()

    if not proposer_team or proposer_team.user_id != current_user.id:
        raise forbidden("Only the proposer can cancel this trade")

    trade.status = TradeStatus.CANCELLED
    trade.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(trade)

    response = await build_trade_response(trade, db)

    # Broadcast cancellation
    await trade_manager.broadcast(trade.season_id, {
        "event": "trade_cancelled",
        "data": {"trade_id": str(trade.id)}
    })

    return response


@router.post("/{trade_id}/approve", response_model=Trade)
async def approve_trade(
    trade_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a trade (league owner only, if approval required)."""
    result = await db.execute(
        select(TradeModel).where(TradeModel.id == trade_id)
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise trade_not_found(trade_id)

    if trade.status != TradeStatus.ACCEPTED:
        raise bad_request("Trade must be accepted before approval")

    if not trade.requires_approval:
        raise bad_request("Trade does not require approval")

    # Get season and verify user is league owner
    season_result = await db.execute(
        select(SeasonModel).where(SeasonModel.id == trade.season_id)
    )
    season = season_result.scalar_one_or_none()

    league_result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = league_result.scalar_one_or_none()

    if not league or league.owner_id != current_user.id:
        raise not_league_owner()

    # Execute the trade
    await execute_trade(trade, db)
    trade.admin_approved = True
    trade.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(trade)

    response = await build_trade_response(trade, db)

    # Broadcast approval
    await trade_manager.broadcast(trade.season_id, {
        "event": "trade_approved",
        "data": {"trade_id": str(trade.id), "trade": response}
    })

    return response


async def execute_trade(trade: TradeModel, db: AsyncSession):
    """
    Execute the actual pokemon swap.

    This function modifies DraftPick records to reassign team ownership.
    The caller is responsible for committing the transaction.
    """
    # Fetch all pokemon (DraftPick records) in a single query for efficiency
    all_pokemon_ids = list(trade.proposer_pokemon) + list(trade.recipient_pokemon)
    pokemon_result = await db.execute(
        select(DraftPick).where(DraftPick.id.in_(all_pokemon_ids))
    )
    pokemon_map = {p.id: p for p in pokemon_result.scalars().all()}

    # Move proposer's pokemon to recipient
    for pokemon_id in trade.proposer_pokemon:
        pokemon = pokemon_map.get(pokemon_id)
        if pokemon:
            pokemon.team_id = trade.recipient_team_id

    # Move recipient's pokemon to proposer
    for pokemon_id in trade.recipient_pokemon:
        pokemon = pokemon_map.get(pokemon_id)
        if pokemon:
            pokemon.team_id = trade.proposer_team_id
