from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID

from app.core.security import get_current_user, get_current_user_optional
from app.schemas.team import Team, TeamCreate, TeamPokemon

router = APIRouter()


@router.get("", response_model=list[Team])
async def list_teams(
    season_id: UUID = Query(..., description="Season to list teams for"),
    current_user=Depends(get_current_user_optional),
):
    """List all teams in a season."""
    # TODO: Implement team listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{team_id}", response_model=Team)
async def get_team(
    team_id: UUID,
    current_user=Depends(get_current_user_optional),
):
    """Get team details including Pokemon roster."""
    # TODO: Implement team retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{team_id}/pokemon", response_model=list[TeamPokemon])
async def get_team_pokemon(
    team_id: UUID,
    current_user=Depends(get_current_user_optional),
):
    """Get all Pokemon on a team."""
    # TODO: Implement team Pokemon listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.put("/{team_id}", response_model=Team)
async def update_team(
    team_id: UUID,
    update: TeamCreate,
    current_user=Depends(get_current_user),
):
    """Update team details (name, etc.)."""
    # TODO: Implement team update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )
