from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.core.security import get_current_user
from app.schemas.league import League, LeagueCreate, LeagueUpdate, LeagueInvite, LeagueMember
from app.schemas.season import Season, SeasonCreate

router = APIRouter()


@router.post("", response_model=League, status_code=status.HTTP_201_CREATED)
async def create_league(
    league: LeagueCreate,
    current_user=Depends(get_current_user),
):
    """Create a new league."""
    # TODO: Implement league creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("", response_model=list[League])
async def list_user_leagues(current_user=Depends(get_current_user)):
    """List leagues the current user is a member of."""
    # TODO: Implement league listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/public", response_model=list[League])
async def list_public_leagues(
    skip: int = 0,
    limit: int = 20,
):
    """List public leagues available to join."""
    # TODO: Implement public league listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{league_id}", response_model=League)
async def get_league(
    league_id: UUID,
    current_user=Depends(get_current_user),
):
    """Get league details."""
    # TODO: Implement league retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.put("/{league_id}", response_model=League)
async def update_league(
    league_id: UUID,
    update: LeagueUpdate,
    current_user=Depends(get_current_user),
):
    """Update league settings (owner only)."""
    # TODO: Implement league update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{league_id}/join", response_model=League)
async def join_league(
    league_id: UUID,
    invite_code: str = None,
    current_user=Depends(get_current_user),
):
    """Join a league via invite code."""
    # TODO: Implement league joining
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.delete("/{league_id}/leave")
async def leave_league(
    league_id: UUID,
    current_user=Depends(get_current_user),
):
    """Leave a league."""
    # TODO: Implement league leaving
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{league_id}/members", response_model=list[LeagueMember])
async def get_league_members(
    league_id: UUID,
    current_user=Depends(get_current_user),
):
    """Get all members of a league."""
    # TODO: Implement member listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.delete("/{league_id}/members/{user_id}")
async def remove_league_member(
    league_id: UUID,
    user_id: UUID,
    current_user=Depends(get_current_user),
):
    """Remove a member from the league (owner only)."""
    # TODO: Implement member removal
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{league_id}/invite", response_model=LeagueInvite)
async def regenerate_invite(
    league_id: UUID,
    current_user=Depends(get_current_user),
):
    """Regenerate league invite code (owner only)."""
    # TODO: Implement invite regeneration
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{league_id}/seasons", response_model=Season, status_code=status.HTTP_201_CREATED)
async def create_season(
    league_id: UUID,
    season: SeasonCreate,
    current_user=Depends(get_current_user),
):
    """Start a new season in the league (owner only)."""
    # TODO: Implement season creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{league_id}/seasons", response_model=list[Season])
async def list_seasons(
    league_id: UUID,
    current_user=Depends(get_current_user),
):
    """List all seasons in a league."""
    # TODO: Implement season listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )
