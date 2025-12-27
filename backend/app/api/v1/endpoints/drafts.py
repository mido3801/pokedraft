from fastapi import APIRouter, Depends, status, Query
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    get_current_user,
    get_current_user_optional,
    generate_session_token,
    generate_rejoin_code,
)
from app.core.config import settings
from app.core.errors import (
    season_not_found,
    draft_not_found,
    team_not_found,
    not_league_owner,
    bad_request,
    forbidden,
    unauthorized,
)
from app.core.auth import get_season as fetch_season
from app.schemas.draft import (
    Draft,
    DraftCreate,
    DraftState,
    AnonymousDraftCreate,
    AnonymousDraftResponse,
    PokemonPoolEntry,
    PokemonFilters,
)
from app.schemas.team import ShowdownExport
from app.models.draft import Draft as DraftModel, DraftPick, DraftStatus
from app.models.season import Season as SeasonModel
from app.models.league import League as LeagueModel, LeagueMembership
from app.models.team import Team as TeamModel
from app.models.user import User
from app.services.team_export import team_export_service
from app.services.pokeapi import pokeapi_service

router = APIRouter()


@router.post("", response_model=Draft, status_code=status.HTTP_201_CREATED)
async def create_draft(
    draft: DraftCreate,
    season_id: UUID = Query(..., description="Season to create draft for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a draft for a season (league owner only)."""
    season = await fetch_season(season_id, db)

    # Check if season already has a draft
    existing_result = await db.execute(
        select(DraftModel).where(DraftModel.season_id == season_id)
    )
    if existing_result.scalar_one_or_none():
        raise bad_request("Season already has a draft")

    # Verify user is league owner
    league_result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = league_result.scalar_one_or_none()

    if not league or league.owner_id != current_user.id:
        raise not_league_owner()

    # Build pokemon pool - load from database if not provided
    pokemon_pool = {}
    if draft.pokemon_pool:
        for entry in draft.pokemon_pool:
            pokemon_pool[str(entry.pokemon_id)] = {
                "name": entry.name,
                "points": entry.points,
                "types": entry.types,
                "generation": entry.generation,
            }
    else:
        # Load all Pokemon from database with full metadata
        all_pokemon = await pokeapi_service.get_all_pokemon_for_box(db)

        # Apply filters if provided
        if draft.pokemon_filters:
            all_pokemon = _apply_pokemon_filters(all_pokemon, draft.pokemon_filters)

        for p in all_pokemon:
            pokemon_pool[str(p["id"])] = {
                "name": p["name"],
                "points": None,
                "types": p["types"],
                "generation": p.get("generation"),
                "bst": p.get("bst"),
                "evolution_stage": p.get("evolution_stage"),
                "is_legendary": p.get("is_legendary", False),
                "is_mythical": p.get("is_mythical", False),
            }

    # Generate draft ID explicitly so we can use it for teams
    import uuid
    draft_id = uuid.uuid4()

    db_draft = DraftModel(
        id=draft_id,
        season_id=season_id,
        format=draft.format,
        timer_seconds=draft.timer_seconds,
        budget_enabled=draft.budget_enabled,
        budget_per_team=draft.budget_per_team,
        roster_size=draft.roster_size,
        pokemon_pool=pokemon_pool,
        nomination_timer_seconds=draft.nomination_timer_seconds,
        min_bid=draft.min_bid,
        bid_increment=draft.bid_increment,
    )
    db.add(db_draft)

    # Get all league members to create teams
    members_result = await db.execute(
        select(LeagueMembership, User)
        .join(User, LeagueMembership.user_id == User.id)
        .where(LeagueMembership.league_id == league.id)
        .where(LeagueMembership.is_active == True)
    )
    members = members_result.all()

    # Re-order: creator first, then others in order
    ordered_members = []
    for membership, user in members:
        if user.id == current_user.id:
            ordered_members.insert(0, (membership, user))
        else:
            ordered_members.append((membership, user))

    creator_team_id = None

    for position, (membership, user) in enumerate(ordered_members):
        team_id = uuid.uuid4()
        team = TeamModel(
            id=team_id,
            draft_id=draft_id,
            season_id=season_id,
            user_id=user.id,
            display_name=user.display_name or user.email.split('@')[0],
            draft_position=position,
            budget_remaining=draft.budget_per_team if draft.budget_enabled else None,
        )
        db.add(team)

        # Track creator's team_id
        if user.id == current_user.id:
            creator_team_id = team_id

    await db.commit()
    await db.refresh(db_draft)

    # Return draft with creator's team_id
    return {
        "id": db_draft.id,
        "season_id": db_draft.season_id,
        "format": db_draft.format,
        "timer_seconds": db_draft.timer_seconds,
        "budget_enabled": db_draft.budget_enabled,
        "budget_per_team": db_draft.budget_per_team,
        "roster_size": db_draft.roster_size,
        "status": db_draft.status,
        "current_pick": db_draft.current_pick,
        "pokemon_pool": db_draft.pokemon_pool,
        "pick_order": db_draft.pick_order,
        "created_at": db_draft.created_at,
        "started_at": db_draft.started_at,
        "completed_at": db_draft.completed_at,
        "team_id": str(creator_team_id) if creator_team_id else None,
    }


def _apply_pokemon_filters(pokemon_list: list[dict], filters: PokemonFilters) -> list[dict]:
    """Apply filters to a list of Pokemon and return filtered list."""
    filtered = []
    custom_inclusions_set = set(filters.custom_inclusions)
    custom_exclusions_set = set(filters.custom_exclusions)

    for p in pokemon_list:
        pokemon_id = p["id"]

        # Force include if in custom_inclusions (overrides all filters)
        if pokemon_id in custom_inclusions_set:
            filtered.append(p)
            continue

        # Skip if in custom_exclusions
        if pokemon_id in custom_exclusions_set:
            continue

        # Check generation filter
        gen = p.get("generation")
        if gen is not None and gen not in filters.generations:
            continue

        # Check evolution stage filter
        evo_stage = p.get("evolution_stage")
        if evo_stage is not None and evo_stage not in filters.evolution_stages:
            continue

        # Check legendary filter
        if not filters.include_legendary and p.get("is_legendary", False):
            continue

        # Check mythical filter
        if not filters.include_mythical and p.get("is_mythical", False):
            continue

        # Check type filter (if types specified, Pokemon must have at least one matching type)
        if filters.types:
            pokemon_types = p.get("types", [])
            if not any(t in filters.types for t in pokemon_types):
                continue

        # Check BST filter
        bst = p.get("bst")
        if bst is not None:
            if bst < filters.bst_min or bst > filters.bst_max:
                continue

        filtered.append(p)

    return filtered


@router.post("/anonymous", response_model=AnonymousDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_anonymous_draft(
    draft: AnonymousDraftCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create an anonymous draft session (no auth required)."""
    session_token = generate_session_token()
    rejoin_code = generate_rejoin_code()

    # Build pokemon pool - load from database if not provided
    pokemon_pool = {}
    if draft.pokemon_pool:
        for entry in draft.pokemon_pool:
            pokemon_pool[str(entry.pokemon_id)] = {
                "name": entry.name,
                "points": entry.points,
                "types": entry.types,
                "generation": entry.generation,
            }
    else:
        # Load all Pokemon from database with full metadata
        all_pokemon = await pokeapi_service.get_all_pokemon_for_box(db)

        # Apply filters if provided
        if draft.pokemon_filters:
            all_pokemon = _apply_pokemon_filters(all_pokemon, draft.pokemon_filters)

        for p in all_pokemon:
            pokemon_pool[str(p["id"])] = {
                "name": p["name"],
                "points": None,
                "types": p["types"],
                "generation": p.get("generation"),
                "bst": p.get("bst"),
                "evolution_stage": p.get("evolution_stage"),
                "is_legendary": p.get("is_legendary", False),
                "is_mythical": p.get("is_mythical", False),
            }

    # Generate UUIDs explicitly so they're available before commit
    import uuid
    draft_id = uuid.uuid4()
    team_id = uuid.uuid4()

    db_draft = DraftModel(
        id=draft_id,
        session_token=session_token,
        rejoin_code=rejoin_code,
        format=draft.format,
        timer_seconds=draft.timer_seconds,
        budget_enabled=draft.budget_enabled,
        budget_per_team=draft.budget_per_team,
        roster_size=draft.roster_size,
        pokemon_pool=pokemon_pool,
        expires_at=datetime.utcnow() + timedelta(days=settings.ANONYMOUS_SESSION_EXPIRE_DAYS),
    )
    db.add(db_draft)

    # Create team for the creator
    creator_team = TeamModel(
        id=team_id,
        draft_id=draft_id,
        session_token=session_token,
        display_name=draft.display_name,
        draft_position=0,
        budget_remaining=draft.budget_per_team if draft.budget_enabled else None,
    )
    db.add(creator_team)

    await db.commit()
    await db.refresh(db_draft)
    await db.refresh(creator_team)

    return {
        "id": db_draft.id,
        "season_id": db_draft.season_id,
        "format": db_draft.format,
        "timer_seconds": db_draft.timer_seconds,
        "budget_enabled": db_draft.budget_enabled,
        "budget_per_team": db_draft.budget_per_team,
        "roster_size": db_draft.roster_size,
        "status": db_draft.status,
        "current_pick": db_draft.current_pick,
        "pokemon_pool": db_draft.pokemon_pool,
        "pick_order": db_draft.pick_order,
        "created_at": db_draft.created_at,
        "started_at": db_draft.started_at,
        "completed_at": db_draft.completed_at,
        "session_token": session_token,
        "rejoin_code": rejoin_code,
        "join_url": f"/drafts/anonymous/join?rejoin_code={rejoin_code}",
        "team_id": str(creator_team.id),
    }


@router.post("/anonymous/join")
async def join_anonymous_draft(
    rejoin_code: str = Query(..., description="Rejoin code (e.g., PIKA-7842)"),
    display_name: str = Query(..., description="Display name for this session"),
    db: AsyncSession = Depends(get_db),
):
    """Join an anonymous draft via rejoin code."""
    result = await db.execute(
        select(DraftModel).where(DraftModel.rejoin_code == rejoin_code.upper())
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise draft_not_found()

    if draft.status != DraftStatus.PENDING:
        raise bad_request("Draft has already started")

    if draft.expires_at and draft.expires_at < datetime.utcnow():
        raise bad_request("Draft session has expired")

    # Check if name is already taken
    existing_result = await db.execute(
        select(TeamModel)
        .where(TeamModel.draft_id == draft.id)
        .where(TeamModel.display_name == display_name)
    )
    if existing_result.scalar_one_or_none():
        raise bad_request("Display name already taken")

    # Get current team count for draft position
    count_result = await db.execute(
        select(TeamModel).where(TeamModel.draft_id == draft.id)
    )
    teams = count_result.scalars().all()
    draft_position = len(teams)

    session_token = generate_session_token()
    new_team = TeamModel(
        draft_id=draft.id,
        session_token=session_token,
        display_name=display_name,
        draft_position=draft_position,
        budget_remaining=draft.budget_per_team if draft.budget_enabled else None,
    )
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)

    return {
        "draft_id": draft.id,
        "team_id": new_team.id,
        "session_token": session_token,
        "display_name": display_name,
        "draft_position": draft_position,
    }


@router.get("/{draft_id}", response_model=Draft)
async def get_draft(
    draft_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Get draft details."""
    result = await db.execute(
        select(DraftModel).where(DraftModel.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise draft_not_found(draft_id)

    return draft


@router.get("/{draft_id}/my-team")
async def get_my_team(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's team for this draft (for league drafts)."""
    # Find team by user_id
    result = await db.execute(
        select(TeamModel)
        .where(TeamModel.draft_id == draft_id)
        .where(TeamModel.user_id == current_user.id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise team_not_found()

    return {"team_id": str(team.id), "display_name": team.display_name}


@router.get("/{draft_id}/state", response_model=DraftState)
async def get_draft_state(
    draft_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Get current draft state (for reconnection)."""
    result = await db.execute(
        select(DraftModel).where(DraftModel.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise draft_not_found(draft_id)

    # Get teams
    teams_result = await db.execute(
        select(TeamModel)
        .where(TeamModel.draft_id == draft_id)
        .order_by(TeamModel.draft_position)
    )
    teams = teams_result.scalars().all()

    # Get picks
    picks_result = await db.execute(
        select(DraftPick)
        .where(DraftPick.draft_id == draft_id)
        .order_by(DraftPick.pick_number)
    )
    picks = picks_result.scalars().all()

    # Get picked pokemon IDs
    picked_ids = {pick.pokemon_id for pick in picks}

    # Build available pokemon list
    available = []
    for pid_str, data in draft.pokemon_pool.items():
        pid = int(pid_str)
        if pid not in picked_ids:
            available.append(PokemonPoolEntry(
                pokemon_id=pid,
                name=data.get("name", ""),
                points=data.get("points"),
                types=data.get("types", []),
                generation=data.get("generation"),
            ))

    # Build team data
    team_data = []
    for team in teams:
        team_picks = [p for p in picks if p.team_id == team.id]
        team_data.append({
            "team_id": str(team.id),
            "display_name": team.display_name,
            "draft_position": team.draft_position,
            "budget_remaining": team.budget_remaining,
            "pokemon": [p.pokemon_id for p in team_picks],
        })

    # Build pick data
    pick_data = []
    for pick in picks:
        team = next((t for t in teams if t.id == pick.team_id), None)
        pokemon_data = draft.pokemon_pool.get(str(pick.pokemon_id), {})
        pick_data.append({
            "pick_number": pick.pick_number,
            "team_id": pick.team_id,
            "team_name": team.display_name if team else "Unknown",
            "pokemon_id": pick.pokemon_id,
            "pokemon_name": pokemon_data.get("name", "Unknown"),
            "points_spent": pick.points_spent,
            "picked_at": pick.picked_at,
        })

    return DraftState(
        draft_id=draft.id,
        status=draft.status,
        format=draft.format,
        current_pick=draft.current_pick,
        roster_size=draft.roster_size,
        timer_seconds=draft.timer_seconds,
        timer_end=None,  # Managed by WebSocket
        pick_order=[team.id for team in teams],
        teams=team_data,
        picks=pick_data,
        available_pokemon=available,
        budget_enabled=draft.budget_enabled,
        budget_per_team=draft.budget_per_team,
    )


@router.post("/{draft_id}/start")
async def start_draft(
    draft_id: UUID,
    session_token: Optional[str] = Query(None, description="Session token for anonymous drafts"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Start the draft (creator/owner only)."""
    result = await db.execute(
        select(DraftModel).where(DraftModel.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise draft_not_found(draft_id)

    if draft.status != DraftStatus.PENDING:
        raise bad_request("Draft is not in pending state")

    # Verify authorization - must be draft creator
    if draft.session_token:
        # Anonymous draft - verify session token matches creator
        if session_token != draft.session_token:
            raise forbidden("Only the draft creator can start the draft")
    elif draft.season_id:
        # League draft - verify user is league owner
        if not current_user:
            raise unauthorized()
        season_result = await db.execute(
            select(SeasonModel).where(SeasonModel.id == draft.season_id)
        )
        season = season_result.scalar_one_or_none()
        if season:
            league_result = await db.execute(
                select(LeagueModel).where(LeagueModel.id == season.league_id)
            )
            league = league_result.scalar_one_or_none()
            if not league or league.owner_id != current_user.id:
                raise not_league_owner()

    # Get teams and set pick order
    teams_result = await db.execute(
        select(TeamModel)
        .where(TeamModel.draft_id == draft_id)
        .order_by(TeamModel.draft_position)
    )
    teams = teams_result.scalars().all()

    if len(teams) < 2:
        raise bad_request("Need at least 2 teams to start")

    draft.status = DraftStatus.LIVE
    draft.started_at = datetime.utcnow()
    draft.pick_order = [str(team.id) for team in teams]

    await db.commit()
    await db.refresh(draft)

    return {"message": "Draft started", "draft_id": draft.id}


@router.post("/{draft_id}/pause")
async def pause_draft(
    draft_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Pause the draft (creator/owner only)."""
    result = await db.execute(
        select(DraftModel).where(DraftModel.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise draft_not_found(draft_id)

    if draft.status != DraftStatus.LIVE:
        raise bad_request("Draft is not live")

    draft.status = DraftStatus.PAUSED
    await db.commit()

    return {"message": "Draft paused", "draft_id": draft.id}


@router.post("/{draft_id}/resume")
async def resume_draft(
    draft_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused draft (creator/owner only)."""
    result = await db.execute(
        select(DraftModel).where(DraftModel.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise draft_not_found(draft_id)

    if draft.status != DraftStatus.PAUSED:
        raise bad_request("Draft is not paused")

    draft.status = DraftStatus.LIVE
    await db.commit()

    return {"message": "Draft resumed", "draft_id": draft.id}


@router.get("/{draft_id}/export")
async def export_team(
    draft_id: UUID,
    team_id: UUID = Query(..., description="Team to export"),
    format: str = Query("showdown", description="Export format: showdown, json, csv"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Export a team from the draft."""
    # Get team
    result = await db.execute(
        select(TeamModel).where(TeamModel.id == team_id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise team_not_found(team_id)

    if team.draft_id != draft_id:
        raise bad_request("Team does not belong to this draft")

    # Get team's pokemon
    picks_result = await db.execute(
        select(DraftPick)
        .where(DraftPick.draft_id == draft_id)
        .where(DraftPick.team_id == team_id)
        .order_by(DraftPick.pick_number)
    )
    picks = picks_result.scalars().all()
    pokemon_ids = [pick.pokemon_id for pick in picks]

    if format == "showdown":
        content = await team_export_service.to_showdown(team.display_name, pokemon_ids, db)
        return ShowdownExport(
            content=content,
            filename=f"{team.display_name.replace(' ', '_')}_team.txt",
        )
    elif format == "json":
        return await team_export_service.to_json(team.display_name, pokemon_ids, db)
    elif format == "csv":
        content = await team_export_service.to_csv(team.display_name, pokemon_ids, db)
        return {"content": content, "filename": f"{team.display_name.replace(' ', '_')}_team.csv"}
    else:
        raise bad_request("Invalid format. Use: showdown, json, csv")
