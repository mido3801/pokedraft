from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from datetime import datetime
from typing import Optional
from itertools import combinations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.match import Match, MatchResult, Standings, TeamStanding, ScheduleGenerateRequest
from app.models.match import Match as MatchModel
from app.models.team import Team as TeamModel
from app.models.season import Season as SeasonModel
from app.models.league import League as LeagueModel
from app.models.user import User

router = APIRouter()


async def match_to_response(match: MatchModel, db: AsyncSession) -> dict:
    """Convert match to response dict with team names."""
    team_a_result = await db.execute(
        select(TeamModel).where(TeamModel.id == match.team_a_id)
    )
    team_a = team_a_result.scalar_one_or_none()

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
    }


@router.get("/schedule", response_model=list[Match])
async def get_schedule(
    season_id: UUID = Query(..., description="Season to get schedule for"),
    week: int = Query(None, description="Filter by week"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the schedule for a season."""
    query = select(MatchModel).where(MatchModel.season_id == season_id)
    if week is not None:
        query = query.where(MatchModel.week == week)

    result = await db.execute(query.order_by(MatchModel.week, MatchModel.created_at))
    matches = result.scalars().all()

    response = []
    for match in matches:
        match_data = await match_to_response(match, db)
        response.append(match_data)

    return response


@router.post("/schedule", response_model=list[Match], status_code=status.HTTP_201_CREATED)
async def generate_schedule(
    season_id: UUID = Query(..., description="Season to generate schedule for"),
    request: ScheduleGenerateRequest = ScheduleGenerateRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a schedule for a season (league owner only)."""
    # Get season
    season_result = await db.execute(
        select(SeasonModel).where(SeasonModel.id == season_id)
    )
    season = season_result.scalar_one_or_none()

    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # Verify user is league owner
    league_result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = league_result.scalar_one_or_none()

    if not league or league.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the league owner can generate schedules")

    # Check if schedule already exists
    existing_result = await db.execute(
        select(MatchModel).where(MatchModel.season_id == season_id)
    )
    if existing_result.scalars().first():
        raise HTTPException(status_code=400, detail="Schedule already exists for this season")

    # Get teams in the season
    teams_result = await db.execute(
        select(TeamModel).where(TeamModel.season_id == season_id)
    )
    teams = teams_result.scalars().all()

    if len(teams) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 teams to generate a schedule")

    team_ids = [team.id for team in teams]
    matches = []

    if request.format == "round_robin":
        # Each team plays every other team once
        matchups = list(combinations(team_ids, 2))
        num_teams = len(team_ids)
        games_per_week = num_teams // 2

        for i, (team_a, team_b) in enumerate(matchups):
            week = (i // games_per_week) + 1
            match = MatchModel(
                season_id=season_id,
                week=week,
                team_a_id=team_a,
                team_b_id=team_b,
            )
            db.add(match)
            matches.append(match)

    elif request.format == "double_round_robin":
        # Each team plays every other team twice
        matchups = list(combinations(team_ids, 2))
        num_teams = len(team_ids)
        games_per_week = num_teams // 2

        # First round
        for i, (team_a, team_b) in enumerate(matchups):
            week = (i // games_per_week) + 1
            match = MatchModel(
                season_id=season_id,
                week=week,
                team_a_id=team_a,
                team_b_id=team_b,
            )
            db.add(match)
            matches.append(match)

        # Second round (reversed home/away)
        first_round_weeks = len(matchups) // games_per_week + (1 if len(matchups) % games_per_week else 0)
        for i, (team_a, team_b) in enumerate(matchups):
            week = first_round_weeks + (i // games_per_week) + 1
            match = MatchModel(
                season_id=season_id,
                week=week,
                team_a_id=team_b,
                team_b_id=team_a,
            )
            db.add(match)
            matches.append(match)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

    await db.commit()

    response = []
    for match in matches:
        await db.refresh(match)
        match_data = await match_to_response(match, db)
        response.append(match_data)

    return response


@router.get("/standings", response_model=Standings)
async def get_standings(
    season_id: UUID = Query(..., description="Season to get standings for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current standings for a season."""
    # Get all teams in the season
    teams_result = await db.execute(
        select(TeamModel).where(TeamModel.season_id == season_id)
    )
    teams = teams_result.scalars().all()

    if not teams:
        raise HTTPException(status_code=404, detail="No teams found for this season")

    standings = []
    for team in teams:
        standings.append(TeamStanding(
            team_id=team.id,
            team_name=team.display_name,
            wins=team.wins,
            losses=team.losses,
            ties=team.ties,
            points=(team.wins * 3) + (team.ties * 1),
            games_played=team.wins + team.losses + team.ties,
        ))

    # Sort by points (descending), then wins, then ties
    standings.sort(key=lambda x: (x.points, x.wins, x.ties), reverse=True)

    return Standings(
        season_id=season_id,
        standings=standings,
    )


@router.get("/{match_id}", response_model=Match)
async def get_match(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get match details."""
    result = await db.execute(
        select(MatchModel).where(MatchModel.id == match_id)
    )
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    return await match_to_response(match, db)


@router.post("/{match_id}/result", response_model=Match)
async def record_result(
    match_id: UUID,
    result: MatchResult,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a match result."""
    match_result = await db.execute(
        select(MatchModel).where(MatchModel.id == match_id)
    )
    match = match_result.scalar_one_or_none()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Validate winner is one of the teams
    if result.winner_id and result.winner_id not in [match.team_a_id, match.team_b_id]:
        raise HTTPException(status_code=400, detail="Winner must be one of the match teams")

    if result.is_tie and result.winner_id:
        raise HTTPException(status_code=400, detail="Cannot have both a tie and a winner")

    # Update match
    match.winner_id = result.winner_id
    match.is_tie = result.is_tie
    match.replay_url = result.replay_url
    match.notes = result.notes
    match.recorded_at = datetime.utcnow()

    # Update team records
    team_a_result = await db.execute(
        select(TeamModel).where(TeamModel.id == match.team_a_id)
    )
    team_a = team_a_result.scalar_one_or_none()

    team_b_result = await db.execute(
        select(TeamModel).where(TeamModel.id == match.team_b_id)
    )
    team_b = team_b_result.scalar_one_or_none()

    if team_a and team_b:
        if result.is_tie:
            team_a.ties += 1
            team_b.ties += 1
        elif result.winner_id == match.team_a_id:
            team_a.wins += 1
            team_b.losses += 1
        elif result.winner_id == match.team_b_id:
            team_b.wins += 1
            team_a.losses += 1

    await db.commit()
    await db.refresh(match)

    return await match_to_response(match, db)
