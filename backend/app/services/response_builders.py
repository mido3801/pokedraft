"""
Response builders for API endpoints.

Centralizes the logic for building enriched API responses from database models.
This reduces duplication across endpoint files and ensures consistent response formats.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.league import League as LeagueModel, LeagueMembership
from app.models.season import Season as SeasonModel
from app.models.team import Team as TeamModel
from app.models.match import Match as MatchModel
from app.models.trade import Trade as TradeModel
from app.models.draft import DraftPick
from app.services.pokeapi import pokeapi_service
from app.services.bracket import get_round_name


async def get_league_member_count(league_id: UUID, db: AsyncSession) -> int:
    """Get the count of active members in a league."""
    result = await db.execute(
        select(func.count(LeagueMembership.id))
        .where(LeagueMembership.league_id == league_id)
        .where(LeagueMembership.is_active == True)
    )
    return result.scalar() or 0


async def get_league_current_season(league_id: UUID, db: AsyncSession) -> Optional[int]:
    """Get the current (highest) season number for a league."""
    result = await db.execute(
        select(func.max(SeasonModel.season_number))
        .where(SeasonModel.league_id == league_id)
    )
    return result.scalar()


async def build_league_response(
    league: LeagueModel,
    db: AsyncSession,
    member_count: Optional[int] = None,
    current_season: Optional[int] = None,
) -> dict:
    """
    Build a league response with enriched data.

    If member_count or current_season are not provided, they will be fetched.
    """
    if member_count is None:
        member_count = await get_league_member_count(league.id, db)

    if current_season is None:
        current_season = await get_league_current_season(league.id, db)

    return {
        "id": league.id,
        "name": league.name,
        "owner_id": league.owner_id,
        "invite_code": league.invite_code,
        "is_public": league.is_public,
        "description": league.description,
        "settings": league.settings,
        "created_at": league.created_at,
        "member_count": member_count,
        "current_season": current_season,
    }


async def build_team_response(team: TeamModel, db: AsyncSession) -> dict:
    """Build a team response with Pokemon roster data."""
    # Get team's pokemon from draft picks
    picks_result = await db.execute(
        select(DraftPick)
        .where(DraftPick.team_id == team.id)
        .order_by(DraftPick.pick_number)
    )
    picks = picks_result.scalars().all()

    # Batch fetch Pokemon data
    pokemon_ids = [pick.pokemon_id for pick in picks]
    pokemon_data_map = await pokeapi_service.get_pokemon_batch(pokemon_ids, db)

    pokemon_list = []
    for pick in picks:
        pokemon_data = pokemon_data_map.get(pick.pokemon_id)
        pokemon_list.append({
            "id": pick.id,
            "pokemon_id": pick.pokemon_id,
            "pokemon_name": pokemon_data["name"] if pokemon_data else "Unknown",
            "pick_number": pick.pick_number,
            "acquisition_type": "drafted",
            "points_spent": pick.points_spent,
            "acquired_at": pick.picked_at,
            "types": pokemon_data["types"] if pokemon_data else [],
            "sprite_url": pokemon_data["sprite"] if pokemon_data else None,
        })

    return {
        "id": team.id,
        "season_id": team.season_id,
        "user_id": team.user_id,
        "display_name": team.display_name,
        "draft_position": team.draft_position,
        "budget_remaining": team.budget_remaining,
        "wins": team.wins,
        "losses": team.losses,
        "ties": team.ties,
        "created_at": team.created_at,
        "pokemon": pokemon_list,
    }


async def build_match_response(
    match: MatchModel,
    db: AsyncSession,
    total_rounds: int = 0,
) -> dict:
    """Build a match response with team names and round info."""
    team_a = None
    team_b = None

    if match.team_a_id:
        team_a_result = await db.execute(
            select(TeamModel).where(TeamModel.id == match.team_a_id)
        )
        team_a = team_a_result.scalar_one_or_none()

    if match.team_b_id:
        team_b_result = await db.execute(
            select(TeamModel).where(TeamModel.id == match.team_b_id)
        )
        team_b = team_b_result.scalar_one_or_none()

    winner_name = None
    if match.winner_id:
        if match.winner_id == match.team_a_id:
            winner_name = team_a.display_name if team_a else None
        else:
            winner_name = team_b.display_name if team_b else None

    # Compute round name for bracket matches
    round_name = None
    if match.bracket_round is not None and total_rounds > 0:
        is_losers = match.bracket_round < 0
        round_name = get_round_name(match.bracket_round, total_rounds, is_losers)
        if match.is_bracket_reset:
            round_name = "Grand Finals Reset"

    return {
        "id": match.id,
        "season_id": match.season_id,
        "week": match.week,
        "team_a_id": match.team_a_id,
        "team_b_id": match.team_b_id,
        "team_a_name": team_a.display_name if team_a else None,
        "team_b_name": team_b.display_name if team_b else None,
        "winner_id": match.winner_id,
        "winner_name": winner_name,
        "is_tie": match.is_tie,
        "scheduled_at": match.scheduled_at,
        "replay_url": match.replay_url,
        "notes": match.notes,
        "recorded_at": match.recorded_at,
        "created_at": match.created_at,
        # Bracket-specific fields
        "schedule_format": match.schedule_format,
        "bracket_round": match.bracket_round,
        "bracket_position": match.bracket_position,
        "next_match_id": match.next_match_id,
        "loser_next_match_id": match.loser_next_match_id,
        "seed_a": match.seed_a,
        "seed_b": match.seed_b,
        "is_bye": match.is_bye,
        "is_bracket_reset": match.is_bracket_reset,
        "round_name": round_name,
    }


async def build_trade_response(trade: TradeModel, db: AsyncSession) -> dict:
    """Build a trade response with team and Pokemon details."""
    # Get team names
    proposer_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.proposer_team_id)
    )
    proposer_team = proposer_result.scalar_one_or_none()

    recipient_result = await db.execute(
        select(TeamModel).where(TeamModel.id == trade.recipient_team_id)
    )
    recipient_team = recipient_result.scalar_one_or_none()

    # Batch fetch all DraftPick records (Pokemon ownership)
    all_pokemon_ids = list(trade.proposer_pokemon) + list(trade.recipient_pokemon)

    # Get DraftPick records
    draft_pick_result = await db.execute(
        select(DraftPick).where(DraftPick.id.in_(all_pokemon_ids))
    )
    draft_pick_map = {dp.id: dp for dp in draft_pick_result.scalars().all()}

    # Get Pokemon data in batch
    pokemon_ids = [dp.pokemon_id for dp in draft_pick_map.values()]
    pokemon_data_map = await pokeapi_service.get_pokemon_batch(pokemon_ids, db)

    # Build proposer pokemon details
    proposer_pokemon_details = []
    for pokemon_id in trade.proposer_pokemon:
        draft_pick = draft_pick_map.get(pokemon_id)
        if draft_pick:
            pokemon_data = pokemon_data_map.get(draft_pick.pokemon_id)
            proposer_pokemon_details.append({
                "id": str(pokemon_id),
                "pokemon_id": draft_pick.pokemon_id,
                "name": pokemon_data["name"] if pokemon_data else "Unknown",
                "types": pokemon_data["types"] if pokemon_data else [],
            })

    # Build recipient pokemon details
    recipient_pokemon_details = []
    for pokemon_id in trade.recipient_pokemon:
        draft_pick = draft_pick_map.get(pokemon_id)
        if draft_pick:
            pokemon_data = pokemon_data_map.get(draft_pick.pokemon_id)
            recipient_pokemon_details.append({
                "id": str(pokemon_id),
                "pokemon_id": draft_pick.pokemon_id,
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
