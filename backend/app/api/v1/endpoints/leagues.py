from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, generate_invite_code
from app.schemas.league import League, LeagueCreate, LeagueUpdate, LeagueInvite, LeagueMember
from app.schemas.season import Season, SeasonCreate
from app.models.league import League as LeagueModel, LeagueMembership
from app.models.season import Season as SeasonModel
from app.models.user import User

router = APIRouter()


def league_to_response(league: LeagueModel, member_count: int = None, current_season: int = None) -> dict:
    """Convert League model to response dict."""
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


@router.post("", response_model=League, status_code=status.HTTP_201_CREATED)
async def create_league(
    league: LeagueCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new league."""
    db_league = LeagueModel(
        name=league.name,
        owner_id=current_user.id,
        invite_code=generate_invite_code(),
        is_public=league.is_public,
        description=league.description,
        settings=league.settings.model_dump(),
    )
    db.add(db_league)

    # Add owner as first member
    membership = LeagueMembership(
        league_id=db_league.id,
        user_id=current_user.id,
    )
    db.add(membership)

    await db.commit()
    await db.refresh(db_league)

    return league_to_response(db_league, member_count=1, current_season=None)


@router.get("", response_model=list[League])
async def list_user_leagues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List leagues the current user is a member of."""
    result = await db.execute(
        select(LeagueModel)
        .join(LeagueMembership)
        .where(LeagueMembership.user_id == current_user.id)
        .where(LeagueMembership.is_active == True)
    )
    leagues = result.scalars().all()

    response = []
    for league in leagues:
        # Get member count
        count_result = await db.execute(
            select(func.count(LeagueMembership.id))
            .where(LeagueMembership.league_id == league.id)
            .where(LeagueMembership.is_active == True)
        )
        member_count = count_result.scalar()

        # Get current season number
        season_result = await db.execute(
            select(func.max(SeasonModel.season_number))
            .where(SeasonModel.league_id == league.id)
        )
        current_season = season_result.scalar()

        response.append(league_to_response(league, member_count, current_season))

    return response


@router.get("/public", response_model=list[League])
async def list_public_leagues(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List public leagues available to join."""
    result = await db.execute(
        select(LeagueModel)
        .where(LeagueModel.is_public == True)
        .offset(skip)
        .limit(limit)
    )
    leagues = result.scalars().all()

    response = []
    for league in leagues:
        count_result = await db.execute(
            select(func.count(LeagueMembership.id))
            .where(LeagueMembership.league_id == league.id)
            .where(LeagueMembership.is_active == True)
        )
        member_count = count_result.scalar()

        season_result = await db.execute(
            select(func.max(SeasonModel.season_number))
            .where(SeasonModel.league_id == league.id)
        )
        current_season = season_result.scalar()

        response.append(league_to_response(league, member_count, current_season))

    return response


@router.get("/{league_id}", response_model=League)
async def get_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get league details."""
    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == league_id)
    )
    league = result.scalar_one_or_none()

    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Check if user is a member or league is public
    membership_result = await db.execute(
        select(LeagueMembership)
        .where(LeagueMembership.league_id == league_id)
        .where(LeagueMembership.user_id == current_user.id)
        .where(LeagueMembership.is_active == True)
    )
    is_member = membership_result.scalar_one_or_none() is not None

    if not is_member and not league.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to view this league")

    count_result = await db.execute(
        select(func.count(LeagueMembership.id))
        .where(LeagueMembership.league_id == league.id)
        .where(LeagueMembership.is_active == True)
    )
    member_count = count_result.scalar()

    season_result = await db.execute(
        select(func.max(SeasonModel.season_number))
        .where(SeasonModel.league_id == league.id)
    )
    current_season = season_result.scalar()

    return league_to_response(league, member_count, current_season)


@router.put("/{league_id}", response_model=League)
async def update_league(
    league_id: UUID,
    update: LeagueUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update league settings (owner only)."""
    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == league_id)
    )
    league = result.scalar_one_or_none()

    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    if league.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can update league settings")

    if update.name is not None:
        league.name = update.name
    if update.is_public is not None:
        league.is_public = update.is_public
    if update.description is not None:
        league.description = update.description
    if update.settings is not None:
        league.settings = update.settings.model_dump()

    await db.commit()
    await db.refresh(league)

    count_result = await db.execute(
        select(func.count(LeagueMembership.id))
        .where(LeagueMembership.league_id == league.id)
        .where(LeagueMembership.is_active == True)
    )
    member_count = count_result.scalar()

    season_result = await db.execute(
        select(func.max(SeasonModel.season_number))
        .where(SeasonModel.league_id == league.id)
    )
    current_season = season_result.scalar()

    return league_to_response(league, member_count, current_season)


@router.post("/{league_id}/join", response_model=League)
async def join_league(
    league_id: UUID,
    invite_code: str = Query(None, description="Invite code for private leagues"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a league via invite code."""
    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == league_id)
    )
    league = result.scalar_one_or_none()

    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Check if already a member
    membership_result = await db.execute(
        select(LeagueMembership)
        .where(LeagueMembership.league_id == league_id)
        .where(LeagueMembership.user_id == current_user.id)
    )
    existing = membership_result.scalar_one_or_none()

    if existing:
        if existing.is_active:
            raise HTTPException(status_code=400, detail="Already a member of this league")
        else:
            # Reactivate membership
            existing.is_active = True
            await db.commit()
    else:
        # Validate invite code for private leagues
        if not league.is_public:
            if not invite_code or invite_code != league.invite_code:
                raise HTTPException(status_code=403, detail="Invalid invite code")

        # Create membership
        membership = LeagueMembership(
            league_id=league_id,
            user_id=current_user.id,
        )
        db.add(membership)
        await db.commit()

    await db.refresh(league)

    count_result = await db.execute(
        select(func.count(LeagueMembership.id))
        .where(LeagueMembership.league_id == league.id)
        .where(LeagueMembership.is_active == True)
    )
    member_count = count_result.scalar()

    season_result = await db.execute(
        select(func.max(SeasonModel.season_number))
        .where(SeasonModel.league_id == league.id)
    )
    current_season = season_result.scalar()

    return league_to_response(league, member_count, current_season)


@router.delete("/{league_id}/leave")
async def leave_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a league."""
    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == league_id)
    )
    league = result.scalar_one_or_none()

    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    if league.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Owner cannot leave the league")

    membership_result = await db.execute(
        select(LeagueMembership)
        .where(LeagueMembership.league_id == league_id)
        .where(LeagueMembership.user_id == current_user.id)
        .where(LeagueMembership.is_active == True)
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=400, detail="Not a member of this league")

    membership.is_active = False
    await db.commit()

    return {"message": "Left league successfully"}


@router.get("/{league_id}/members", response_model=list[LeagueMember])
async def get_league_members(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all members of a league."""
    # Verify user is a member
    membership_check = await db.execute(
        select(LeagueMembership)
        .where(LeagueMembership.league_id == league_id)
        .where(LeagueMembership.user_id == current_user.id)
        .where(LeagueMembership.is_active == True)
    )
    if not membership_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this league")

    result = await db.execute(
        select(LeagueMembership, User)
        .join(User)
        .where(LeagueMembership.league_id == league_id)
        .where(LeagueMembership.is_active == True)
    )
    memberships = result.all()

    return [
        {
            "user_id": user.id,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "joined_at": membership.joined_at,
        }
        for membership, user in memberships
    ]


@router.delete("/{league_id}/members/{user_id}")
async def remove_league_member(
    league_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the league (owner only)."""
    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == league_id)
    )
    league = result.scalar_one_or_none()

    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    if league.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can remove members")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    membership_result = await db.execute(
        select(LeagueMembership)
        .where(LeagueMembership.league_id == league_id)
        .where(LeagueMembership.user_id == user_id)
        .where(LeagueMembership.is_active == True)
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member")

    membership.is_active = False
    await db.commit()

    return {"message": "Member removed successfully"}


@router.post("/{league_id}/invite", response_model=LeagueInvite)
async def regenerate_invite(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate league invite code (owner only)."""
    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == league_id)
    )
    league = result.scalar_one_or_none()

    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    if league.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can regenerate invite code")

    league.invite_code = generate_invite_code()
    await db.commit()

    return {
        "invite_code": league.invite_code,
        "invite_url": f"/leagues/{league_id}/join?invite_code={league.invite_code}",
    }


@router.post("/{league_id}/seasons", response_model=Season, status_code=status.HTTP_201_CREATED)
async def create_season(
    league_id: UUID,
    season: SeasonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new season in the league (owner only)."""
    result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == league_id)
    )
    league = result.scalar_one_or_none()

    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    if league.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can create seasons")

    # Get next season number
    season_result = await db.execute(
        select(func.max(SeasonModel.season_number))
        .where(SeasonModel.league_id == league_id)
    )
    max_season = season_result.scalar() or 0

    db_season = SeasonModel(
        league_id=league_id,
        season_number=max_season + 1,
        keep_teams=season.keep_teams,
        settings=season.settings.model_dump() if season.settings else {},
    )
    db.add(db_season)
    await db.commit()
    await db.refresh(db_season)

    return db_season


@router.get("/{league_id}/seasons", response_model=list[Season])
async def list_seasons(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all seasons in a league."""
    # Verify user is a member
    membership_check = await db.execute(
        select(LeagueMembership)
        .where(LeagueMembership.league_id == league_id)
        .where(LeagueMembership.user_id == current_user.id)
        .where(LeagueMembership.is_active == True)
    )
    if not membership_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this league")

    result = await db.execute(
        select(SeasonModel)
        .where(SeasonModel.league_id == league_id)
        .order_by(SeasonModel.season_number.desc())
    )
    return result.scalars().all()
