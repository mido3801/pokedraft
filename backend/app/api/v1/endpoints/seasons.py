from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.models.season import Season as SeasonModel
from app.models.league import League as LeagueModel, LeagueMembership
from app.models.team import Team as TeamModel
from app.models.draft import Draft as DraftModel
from app.models.user import User

router = APIRouter()


@router.get("/{season_id}")
async def get_season(
    season_id: UUID,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Get season details by ID."""
    result = await db.execute(
        select(SeasonModel, LeagueModel)
        .join(LeagueModel)
        .where(SeasonModel.id == season_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Season not found")

    season, league = row

    # Check access - must be a member of the league or league must be public
    if current_user:
        membership_result = await db.execute(
            select(LeagueMembership)
            .where(LeagueMembership.league_id == league.id)
            .where(LeagueMembership.user_id == current_user.id)
            .where(LeagueMembership.is_active == True)
        )
        is_member = membership_result.scalar_one_or_none() is not None
    else:
        is_member = False

    if not is_member and not league.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to view this season")

    # Get team count
    team_count_result = await db.execute(
        select(func.count(TeamModel.id))
        .where(TeamModel.season_id == season_id)
    )
    team_count = team_count_result.scalar() or 0

    # Get draft_id if exists
    draft_result = await db.execute(
        select(DraftModel.id)
        .where(DraftModel.season_id == season_id)
    )
    draft = draft_result.scalar_one_or_none()

    return {
        "id": season.id,
        "league_id": season.league_id,
        "league_name": league.name,
        "season_number": season.season_number,
        "status": season.status.value if hasattr(season.status, 'value') else season.status,
        "keep_teams": season.keep_teams,
        "settings": season.settings,
        "started_at": season.started_at,
        "completed_at": season.completed_at,
        "created_at": season.created_at,
        "team_count": team_count,
        "draft_id": str(draft) if draft else None,
    }
