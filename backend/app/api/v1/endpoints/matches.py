import random
from collections import defaultdict
from fastapi import APIRouter, Depends, status, Query
from uuid import UUID
from datetime import datetime
from itertools import combinations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.errors import (
    season_not_found,
    match_not_found,
    not_league_owner,
    bad_request,
    not_found,
)
from app.core.auth import get_season as fetch_season
from app.schemas.match import Match, MatchResult, Standings, TeamStanding, ScheduleGenerateRequest, BracketState
from app.models.match import Match as MatchModel
from app.models.team import Team as TeamModel
from app.models.season import Season as SeasonModel
from app.models.league import League as LeagueModel
from app.models.user import User
from app.services.bracket import (
    generate_single_elimination_bracket,
    generate_double_elimination_bracket,
    process_bracket_progression,
    process_bye_matches,
)
from app.services.response_builders import build_match_response

router = APIRouter()


def compute_total_rounds(matches: list[MatchModel]) -> int:
    """Compute total rounds in bracket from matches."""
    winners_rounds = [m.bracket_round for m in matches if m.bracket_round and m.bracket_round > 0]
    return max(winners_rounds) if winners_rounds else 0


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

    return [await build_match_response(match, db) for match in matches]


@router.post("/schedule", response_model=list[Match], status_code=status.HTTP_201_CREATED)
async def generate_schedule(
    season_id: UUID = Query(..., description="Season to generate schedule for"),
    request: ScheduleGenerateRequest = ScheduleGenerateRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a schedule for a season (league owner only)."""
    season = await fetch_season(season_id, db)

    # Verify user is league owner
    league_result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = league_result.scalar_one_or_none()

    if not league or league.owner_id != current_user.id:
        raise not_league_owner()

    # Check if schedule already exists
    existing_result = await db.execute(
        select(MatchModel).where(MatchModel.season_id == season_id)
    )
    if existing_result.scalars().first():
        raise bad_request("Schedule already exists for this season")

    # Get teams in the season
    teams_result = await db.execute(
        select(TeamModel).where(TeamModel.season_id == season_id)
    )
    teams = teams_result.scalars().all()

    if len(teams) < 2:
        raise bad_request("Need at least 2 teams to generate a schedule")

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
                schedule_format='round_robin',
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
                schedule_format='double_round_robin',
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
                schedule_format='double_round_robin',
            )
            db.add(match)
            matches.append(match)

    elif request.format == "single_elimination":
        # Get seeding
        if request.manual_seeds:
            seeds = request.manual_seeds
        elif request.use_standings_seeding:
            # Get standings to determine seeding
            standings = []
            for team in teams:
                standings.append({
                    'team_id': team.id,
                    'points': (team.wins * 3) + (team.ties * 1),
                    'wins': team.wins,
                    'ties': team.ties,
                })
            standings.sort(key=lambda x: (x['points'], x['wins'], x['ties']), reverse=True)
            seeds = [s['team_id'] for s in standings]
        else:
            # Random seeding
            seeds = list(team_ids)
            random.shuffle(seeds)

        matches = generate_single_elimination_bracket(season_id, team_ids, seeds)

        # Add all matches to session
        for match in matches:
            db.add(match)

        await db.flush()

        # Process bye matches
        bye_results = process_bye_matches(matches)
        for bye_match, winner_id in bye_results:
            await process_bracket_progression(bye_match, winner_id, None, db)

    elif request.format == "double_elimination":
        # Get seeding
        if request.manual_seeds:
            seeds = request.manual_seeds
        elif request.use_standings_seeding:
            standings = []
            for team in teams:
                standings.append({
                    'team_id': team.id,
                    'points': (team.wins * 3) + (team.ties * 1),
                    'wins': team.wins,
                    'ties': team.ties,
                })
            standings.sort(key=lambda x: (x['points'], x['wins'], x['ties']), reverse=True)
            seeds = [s['team_id'] for s in standings]
        else:
            seeds = list(team_ids)
            random.shuffle(seeds)

        matches = generate_double_elimination_bracket(
            season_id, team_ids, seeds, request.include_bracket_reset
        )

        for match in matches:
            db.add(match)

        await db.flush()

        # Process bye matches
        bye_results = process_bye_matches(matches)
        for bye_match, winner_id in bye_results:
            await process_bracket_progression(bye_match, winner_id, None, db)

    else:
        raise bad_request(f"Unsupported format: {request.format}")

    await db.commit()

    total_rounds = compute_total_rounds(matches)
    response = []
    for match in matches:
        await db.refresh(match)
        match_data = await build_match_response(match, db, total_rounds)
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
        raise not_found("Teams", f"in season {season_id}")

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


@router.get("/bracket", response_model=BracketState)
async def get_bracket(
    season_id: UUID = Query(..., description="Season to get bracket for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the bracket state for visual rendering."""
    result = await db.execute(
        select(MatchModel).where(MatchModel.season_id == season_id)
        .order_by(MatchModel.bracket_round, MatchModel.bracket_position)
    )
    matches = result.scalars().all()

    if not matches:
        raise not_found("Schedule", f"for season {season_id}")

    # Check if it's a bracket format
    first_match = matches[0]
    if first_match.schedule_format not in ['single_elimination', 'double_elimination']:
        raise bad_request("Season does not use bracket format")

    format_type = first_match.schedule_format
    total_rounds = compute_total_rounds(matches)

    # Group matches by round
    winners_bracket: dict[int, list] = defaultdict(list)
    losers_bracket: dict[int, list] = defaultdict(list)
    grand_finals: list = []

    # Get unique teams
    team_ids = set()
    for match in matches:
        if match.team_a_id:
            team_ids.add(match.team_a_id)
        if match.team_b_id:
            team_ids.add(match.team_b_id)

    for match in matches:
        match_data = await build_match_response(match, db, total_rounds)

        if match.bracket_round == 0:
            grand_finals.append(match_data)
        elif match.bracket_round is not None and match.bracket_round < 0:
            losers_bracket[abs(match.bracket_round)].append(match_data)
        elif match.bracket_round is not None and match.bracket_round > 0:
            winners_bracket[match.bracket_round].append(match_data)

    # Sort by position within each round
    for round_matches in winners_bracket.values():
        round_matches.sort(key=lambda m: m.get('bracket_position', 0))
    for round_matches in losers_bracket.values():
        round_matches.sort(key=lambda m: m.get('bracket_position', 0))

    # Determine champion
    champion_id = None
    champion_name = None
    if grand_finals:
        # For double elim, check bracket reset first
        reset_match = next((m for m in grand_finals if m.get('is_bracket_reset')), None)
        regular_gf = next((m for m in grand_finals if not m.get('is_bracket_reset')), None)

        if reset_match and reset_match.get('winner_id'):
            champion_id = reset_match.get('winner_id')
            champion_name = reset_match.get('winner_name')
        elif regular_gf and regular_gf.get('winner_id'):
            # Check if winners bracket champion won (no reset needed)
            if regular_gf.get('winner_id') == regular_gf.get('team_a_id'):
                champion_id = regular_gf.get('winner_id')
                champion_name = regular_gf.get('winner_name')
            elif reset_match is None:
                # Single elim or no reset match exists
                champion_id = regular_gf.get('winner_id')
                champion_name = regular_gf.get('winner_name')
    else:
        # Single elim: check finals
        if total_rounds in winners_bracket:
            finals = winners_bracket[total_rounds]
            if finals and finals[0].get('winner_id'):
                champion_id = finals[0].get('winner_id')
                champion_name = finals[0].get('winner_name')

    return BracketState(
        season_id=season_id,
        format=format_type,
        team_count=len(team_ids),
        total_rounds=total_rounds,
        winners_bracket=[winners_bracket[r] for r in sorted(winners_bracket.keys())],
        losers_bracket=[losers_bracket[r] for r in sorted(losers_bracket.keys())] if losers_bracket else None,
        grand_finals=grand_finals if grand_finals else None,
        champion_id=champion_id,
        champion_name=champion_name,
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
        raise match_not_found(match_id)

    return await build_match_response(match, db)


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
        raise match_not_found(match_id)

    # Validate teams are set
    if not match.team_a_id or not match.team_b_id:
        raise bad_request("Cannot record result for match with pending teams")

    # Validate winner is one of the teams
    if result.winner_id and result.winner_id not in [match.team_a_id, match.team_b_id]:
        raise bad_request("Winner must be one of the match teams")

    if result.is_tie and result.winner_id:
        raise bad_request("Cannot have both a tie and a winner")

    # Bracket matches don't allow ties
    if result.is_tie and match.schedule_format in ['single_elimination', 'double_elimination']:
        raise bad_request("Bracket matches cannot end in a tie")

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

    # Process bracket progression if this is a bracket match
    if match.schedule_format in ['single_elimination', 'double_elimination'] and result.winner_id:
        loser_id = match.team_b_id if result.winner_id == match.team_a_id else match.team_a_id
        await process_bracket_progression(match, result.winner_id, loser_id, db)

    await db.commit()
    await db.refresh(match)

    # Get total rounds for round name computation
    all_matches_result = await db.execute(
        select(MatchModel).where(MatchModel.season_id == match.season_id)
    )
    all_matches = all_matches_result.scalars().all()
    total_rounds = compute_total_rounds(all_matches)

    return await build_match_response(match, db, total_rounds)
