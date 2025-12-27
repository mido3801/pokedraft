from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.core.errors import team_not_found, not_team_owner, bad_request
from app.schemas.team import Team, TeamCreate, TeamPokemon
from app.models.team import Team as TeamModel
from app.models.draft import DraftPick
from app.models.user import User
from app.services.pokeapi import pokeapi_service
from app.services.response_builders import build_team_response

router = APIRouter()


@router.get("", response_model=list[Team])
async def list_teams(
    season_id: UUID = Query(None, description="Season to list teams for"),
    draft_id: UUID = Query(None, description="Draft to list teams for"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """List all teams in a season or draft."""
    if not season_id and not draft_id:
        raise bad_request("Must provide season_id or draft_id")

    query = select(TeamModel)
    if season_id:
        query = query.where(TeamModel.season_id == season_id)
    if draft_id:
        query = query.where(TeamModel.draft_id == draft_id)

    result = await db.execute(query.order_by(TeamModel.draft_position))
    teams = result.scalars().all()

    return [await build_team_response(team, db) for team in teams]


@router.get("/{team_id}", response_model=Team)
async def get_team(
    team_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Get team details including Pokemon roster."""
    result = await db.execute(
        select(TeamModel).where(TeamModel.id == team_id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise team_not_found(team_id)

    return await build_team_response(team, db)


@router.get("/{team_id}/pokemon", response_model=list[TeamPokemon])
async def get_team_pokemon(
    team_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Get all Pokemon on a team."""
    result = await db.execute(
        select(TeamModel).where(TeamModel.id == team_id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise team_not_found(team_id)

    # Get team's pokemon from draft picks
    picks_result = await db.execute(
        select(DraftPick)
        .where(DraftPick.team_id == team_id)
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

    return pokemon_list


@router.put("/{team_id}", response_model=Team)
async def update_team(
    team_id: UUID,
    update: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update team details (name, etc.)."""
    result = await db.execute(
        select(TeamModel).where(TeamModel.id == team_id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise team_not_found(team_id)

    # Verify ownership
    if team.user_id and team.user_id != current_user.id:
        raise not_team_owner()

    team.display_name = update.display_name
    await db.commit()
    await db.refresh(team)

    return await build_team_response(team, db)
