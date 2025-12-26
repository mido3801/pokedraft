from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.schemas.team import Team, TeamCreate, TeamPokemon
from app.models.team import Team as TeamModel, TeamPokemon as TeamPokemonModel
from app.models.draft import DraftPick
from app.models.user import User
from app.services.pokeapi import pokeapi_service

router = APIRouter()


async def build_team_response(team: TeamModel, db: AsyncSession) -> dict:
    """Build team response with Pokemon data."""
    # Get team's pokemon from draft picks or team_pokemon table
    picks_result = await db.execute(
        select(DraftPick)
        .where(DraftPick.team_id == team.id)
        .order_by(DraftPick.pick_number)
    )
    picks = picks_result.scalars().all()

    pokemon_list = []
    for pick in picks:
        pokemon_data = await pokeapi_service.get_pokemon(pick.pokemon_id, db)
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


@router.get("", response_model=list[Team])
async def list_teams(
    season_id: UUID = Query(None, description="Season to list teams for"),
    draft_id: UUID = Query(None, description="Draft to list teams for"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """List all teams in a season or draft."""
    if not season_id and not draft_id:
        raise HTTPException(status_code=400, detail="Must provide season_id or draft_id")

    query = select(TeamModel)
    if season_id:
        query = query.where(TeamModel.season_id == season_id)
    if draft_id:
        query = query.where(TeamModel.draft_id == draft_id)

    result = await db.execute(query.order_by(TeamModel.draft_position))
    teams = result.scalars().all()

    response = []
    for team in teams:
        team_data = await build_team_response(team, db)
        response.append(team_data)

    return response


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
        raise HTTPException(status_code=404, detail="Team not found")

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
        raise HTTPException(status_code=404, detail="Team not found")

    # Get team's pokemon from draft picks
    picks_result = await db.execute(
        select(DraftPick)
        .where(DraftPick.team_id == team_id)
        .order_by(DraftPick.pick_number)
    )
    picks = picks_result.scalars().all()

    pokemon_list = []
    for pick in picks:
        pokemon_data = await pokeapi_service.get_pokemon(pick.pokemon_id, db)
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
        raise HTTPException(status_code=404, detail="Team not found")

    # Verify ownership
    if team.user_id and team.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this team")

    team.display_name = update.display_name
    await db.commit()
    await db.refresh(team)

    return await build_team_response(team, db)
