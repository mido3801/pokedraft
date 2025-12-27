from fastapi import APIRouter, Depends
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.core.errors import season_not_found, not_league_member
from app.core.auth import check_league_membership
from app.models.season import Season as SeasonModel
from app.models.league import League as LeagueModel
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
        raise season_not_found(season_id)

    season, league = row

    # Check access - must be a member of the league or league must be public
    if current_user:
        is_member = await check_league_membership(league.id, current_user, db)
    else:
        is_member = False

    if not is_member and not league.is_public:
        raise not_league_member()

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

    # Check if user is the league owner
    is_owner = current_user is not None and league.owner_id == current_user.id

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
        "is_owner": is_owner,
        "league_settings": league.settings,
    }
