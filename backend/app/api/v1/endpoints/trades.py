from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from datetime import datetime
from typing import Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.trade import Trade, TradeCreate
from app.models.trade import Trade as TradeModel, TradeStatus
from app.models.team import Team as TeamModel, TeamPokemon, AcquisitionType
from app.models.season import Season as SeasonModel, SeasonStatus
from app.models.league import League as LeagueModel
from app.models.user import User
from app.services.pokeapi import pokeapi_service

router = APIRouter()


async def trade_to_response(trade: TradeModel, db: AsyncSession) -> dict:
    """Convert trade to response dict with team and pokemon details."""
    # Get team names
    proposer_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.proposer_team_id)
    )
    proposer_team = proposer_result.scalar_one_or_none()

    recipient_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.recipient_team_id)
    )
    recipient_team = recipient_result.scalar_one_or_none()

    # Get pokemon details
    proposer_pokemon_details = []
    for pokemon_id in trade.proposer_pokemon:
        pokemon_result = await db.execute(
            select(TeamPokemon).where(TeamPokemon.id == pokemon_id)
        )
        team_pokemon = pokemon_result.scalar_one_or_none()
        if team_pokemon:
            pokemon_data = await pokeapi_service.get_pokemon(team_pokemon.pokemon_id, db)
            proposer_pokemon_details.append({
                "id": pokemon_id,
                "pokemon_id": team_pokemon.pokemon_id,
                "name": pokemon_data["name"] if pokemon_data else "Unknown",
                "types": pokemon_data["types"] if pokemon_data else [],
            })

    recipient_pokemon_details = []
    for pokemon_id in trade.recipient_pokemon:
        pokemon_result = await db.execute(
            select(TeamPokemon).where(TeamPokemon.id == pokemon_id)
        )
        team_pokemon = pokemon_result.scalar_one_or_none()
        if team_pokemon:
            pokemon_data = await pokeapi_service.get_pokemon(team_pokemon.pokemon_id, db)
            recipient_pokemon_details.append({
                "id": pokemon_id,
                "pokemon_id": team_pokemon.pokemon_id,
                "name": pokemon_data["name"] if pokemon_data else "Unknown",
                "types": pokemon_data["types"] if pokemon_data else [],
            })

    return {
        "id": trade.id,
        "season_id": trade.season_id,
        "proposer_team_id": trade.proposer_team_id,
        "recipient_team_id": trade.recipient_team_id,
        "proposer_team_name": proposer_team.display_name if proposer_team else None,
        "recipient_team_name": recipient_team.display_name if recipient_team else None,
        "proposer_pokemon": trade.proposer_pokemon,
        "recipient_pokemon": trade.recipient_pokemon,
        "proposer_pokemon_details": proposer_pokemon_details,
        "recipient_pokemon_details": recipient_pokemon_details,
        "status": trade.status,
        "requires_approval": trade.requires_approval,
        "admin_approved": trade.admin_approved,
        "message": trade.message,
        "created_at": trade.created_at,
        "resolved_at": trade.resolved_at,
    }


@router.post("", response_model=Trade, status_code=status.HTTP_201_CREATED)
async def propose_trade(
    trade: TradeCreate,
    season_id: UUID = Query(..., description="Season for the trade"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Propose a trade to another team."""
    # Get season and verify it's active
    season_result = await db.execute(
        select(SeasonModel).where(SeasonModel.id == season_id)
    )
    season = season_result.scalar_one_or_none()

    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    if season.status != SeasonStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Trades can only occur during an active season")

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
        raise HTTPException(status_code=403, detail="You don't have a team in this season")

    # Verify recipient team exists
    recipient_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.recipient_team_id)
    )
    recipient_team = recipient_result.scalar_one_or_none()

    if not recipient_team or recipient_team.season_id != season_id:
        raise HTTPException(status_code=404, detail="Recipient team not found in this season")

    if recipient_team.id == proposer_team.id:
        raise HTTPException(status_code=400, detail="Cannot trade with yourself")

    # Verify proposer owns the pokemon they're offering
    for pokemon_id in trade.proposer_pokemon:
        pokemon_result = await db.execute(
            select(TeamPokemon)
            .where(TeamPokemon.id == pokemon_id)
            .where(TeamPokemon.team_id == proposer_team.id)
        )
        if not pokemon_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"You don't own pokemon {pokemon_id}")

    # Verify recipient owns the pokemon being requested
    for pokemon_id in trade.recipient_pokemon:
        pokemon_result = await db.execute(
            select(TeamPokemon)
            .where(TeamPokemon.id == pokemon_id)
            .where(TeamPokemon.team_id == recipient_team.id)
        )
        if not pokemon_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Recipient doesn't own pokemon {pokemon_id}")

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

    return await trade_to_response(db_trade, db)


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
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")

    result = await db.execute(query.order_by(TradeModel.created_at.desc()))
    trades = result.scalars().all()

    response = []
    for trade in trades:
        trade_data = await trade_to_response(trade, db)
        response.append(trade_data)

    return response


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
        raise HTTPException(status_code=404, detail="Trade not found")

    return await trade_to_response(trade, db)


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
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.status != TradeStatus.PENDING:
        raise HTTPException(status_code=400, detail="Trade is not pending")

    # Verify user owns the recipient team
    recipient_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.recipient_team_id)
    )
    recipient_team = recipient_result.scalar_one_or_none()

    if not recipient_team or recipient_team.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the recipient can accept this trade")

    # If requires approval, set to accepted but wait for admin
    if trade.requires_approval:
        trade.status = TradeStatus.ACCEPTED
        await db.commit()
        await db.refresh(trade)
        return await trade_to_response(trade, db)

    # Execute the trade
    await execute_trade(trade, db)
    trade.status = TradeStatus.ACCEPTED
    trade.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(trade)

    return await trade_to_response(trade, db)


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
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.status != TradeStatus.PENDING:
        raise HTTPException(status_code=400, detail="Trade is not pending")

    # Verify user owns the recipient team
    recipient_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.recipient_team_id)
    )
    recipient_team = recipient_result.scalar_one_or_none()

    if not recipient_team or recipient_team.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the recipient can reject this trade")

    trade.status = TradeStatus.REJECTED
    trade.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(trade)

    return await trade_to_response(trade, db)


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
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.status != TradeStatus.PENDING:
        raise HTTPException(status_code=400, detail="Trade is not pending")

    # Verify user owns the proposer team
    proposer_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.proposer_team_id)
    )
    proposer_team = proposer_result.scalar_one_or_none()

    if not proposer_team or proposer_team.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the proposer can cancel this trade")

    trade.status = TradeStatus.CANCELLED
    trade.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(trade)

    return await trade_to_response(trade, db)


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
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.status != TradeStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="Trade must be accepted before approval")

    if not trade.requires_approval:
        raise HTTPException(status_code=400, detail="Trade does not require approval")

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
        raise HTTPException(status_code=403, detail="Only the league owner can approve trades")

    # Execute the trade
    await execute_trade(trade, db)
    trade.admin_approved = True
    trade.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(trade)

    return await trade_to_response(trade, db)


async def execute_trade(trade: TradeModel, db: AsyncSession):
    """Execute the actual pokemon swap."""
    # Move proposer's pokemon to recipient
    for pokemon_id in trade.proposer_pokemon:
        pokemon_result = await db.execute(
            select(TeamPokemon).where(TeamPokemon.id == pokemon_id)
        )
        pokemon = pokemon_result.scalar_one_or_none()
        if pokemon:
            pokemon.team_id = trade.recipient_team_id
            pokemon.acquisition_type = AcquisitionType.TRADED
            pokemon.acquired_at = datetime.utcnow()

    # Move recipient's pokemon to proposer
    for pokemon_id in trade.recipient_pokemon:
        pokemon_result = await db.execute(
            select(TeamPokemon).where(TeamPokemon.id == pokemon_id)
        )
        pokemon = pokemon_result.scalar_one_or_none()
        if pokemon:
            pokemon.team_id = trade.proposer_team_id
            pokemon.acquisition_type = AcquisitionType.TRADED
            pokemon.acquired_at = datetime.utcnow()
