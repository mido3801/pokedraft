"""
Authorization dependencies for API endpoints.

Provides reusable FastAPI dependencies for common authorization patterns.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.core.errors import (
    league_not_found,
    season_not_found,
    team_not_found,
    draft_not_found,
    not_league_member,
    not_league_owner,
    not_team_owner,
)
from app.models.user import User
from app.models.league import League as LeagueModel, LeagueMembership
from app.models.season import Season as SeasonModel
from app.models.team import Team as TeamModel
from app.models.draft import Draft as DraftModel


async def get_league(
    league_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> LeagueModel:
    """Get a league by ID or raise 404."""
    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == league_id)
    )
    league = result.scalar_one_or_none()
    if not league:
        raise league_not_found(league_id)
    return league


async def get_season(
    season_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SeasonModel:
    """Get a season by ID or raise 404."""
    result = await db.execute(
        select(SeasonModel).where(SeasonModel.id == season_id)
    )
    season = result.scalar_one_or_none()
    if not season:
        raise season_not_found(season_id)
    return season


async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TeamModel:
    """Get a team by ID or raise 404."""
    result = await db.execute(
        select(TeamModel).where(TeamModel.id == team_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise team_not_found(team_id)
    return team


async def get_draft(
    draft_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DraftModel:
    """Get a draft by ID or raise 404."""
    result = await db.execute(
        select(DraftModel).where(DraftModel.id == draft_id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise draft_not_found(draft_id)
    return draft


async def check_league_membership(
    league_id: UUID,
    user: User,
    db: AsyncSession,
) -> bool:
    """Check if a user is an active member of a league."""
    result = await db.execute(
        select(LeagueMembership)
        .where(LeagueMembership.league_id == league_id)
        .where(LeagueMembership.user_id == user.id)
        .where(LeagueMembership.is_active == True)
    )
    return result.scalar_one_or_none() is not None


async def require_league_member(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeagueModel:
    """
    Require the current user to be a member of the league.

    Returns the league if user is a member, raises 403 otherwise.
    """
    league = await get_league(league_id, db)

    is_member = await check_league_membership(league_id, current_user, db)
    if not is_member and not league.is_public:
        raise not_league_member()

    return league


async def require_league_owner(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeagueModel:
    """
    Require the current user to be the owner of the league.

    Returns the league if user is owner, raises 403 otherwise.
    """
    league = await get_league(league_id, db)

    if league.owner_id != current_user.id:
        raise not_league_owner()

    return league


async def require_season_league_owner(
    season_id: UUID = Query(..., description="Season ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[SeasonModel, LeagueModel]:
    """
    Require the current user to be the owner of the season's league.

    Returns (season, league) tuple if user is owner, raises 403 otherwise.
    """
    season = await get_season(season_id, db)

    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = result.scalar_one_or_none()

    if not league or league.owner_id != current_user.id:
        raise not_league_owner()

    return season, league


async def require_season_league_member(
    season_id: UUID = Query(..., description="Season ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[SeasonModel, LeagueModel]:
    """
    Require the current user to be a member of the season's league.

    Returns (season, league) tuple if user is member, raises 403 otherwise.
    """
    season = await get_season(season_id, db)

    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = result.scalar_one_or_none()

    if not league:
        raise league_not_found(season.league_id)

    is_member = await check_league_membership(league.id, current_user, db)
    if not is_member and not league.is_public:
        raise not_league_member()

    return season, league


async def require_team_owner(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamModel:
    """
    Require the current user to own the team.

    Returns the team if user is owner, raises 403 otherwise.
    """
    team = await get_team(team_id, db)

    if team.user_id and team.user_id != current_user.id:
        raise not_team_owner()

    return team


async def get_user_team_in_season(
    season_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[TeamModel]:
    """Get the current user's team in a season, if any."""
    result = await db.execute(
        select(TeamModel)
        .where(TeamModel.season_id == season_id)
        .where(TeamModel.user_id == current_user.id)
    )
    return result.scalar_one_or_none()


async def require_user_team_in_season(
    season_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamModel:
    """
    Require the current user to have a team in the season.

    Returns the team if found, raises 403 otherwise.
    """
    team = await get_user_team_in_season(season_id, current_user, db)
    if not team:
        from app.core.errors import ForbiddenError
        raise ForbiddenError("You don't have a team in this season")
    return team
