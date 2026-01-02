from uuid import UUID
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.core.security import get_current_user
from app.core.errors import (
    waiver_claim_not_found,
    not_league_owner,
    bad_request,
    forbidden,
)
from app.core.auth import get_season as fetch_season
from app.core.constants import LeagueSettings, SeasonSettings
from app.schemas.waiver import (
    WaiverClaimCreate,
    WaiverClaimResponse,
    WaiverClaimList,
    WaiverVoteCreate,
    WaiverVoteResponse,
    WaiverAdminAction,
    FreeAgentPokemon,
    FreeAgentList,
)
from app.models.waiver import (
    WaiverClaim as WaiverClaimModel,
    WaiverClaimStatus,
    WaiverProcessingType,
    WaiverVote as WaiverVoteModel,
)
from app.models.team import Team as TeamModel
from app.models.draft import DraftPick
from app.models.season import Season as SeasonModel, SeasonStatus
from app.models.league import League as LeagueModel, LeagueMembership
from app.models.user import User
from app.services.response_builders import build_waiver_claim_response
from app.websocket.waiver_manager import waiver_manager

router = APIRouter()


@router.post("", response_model=WaiverClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_waiver_claim(
    claim: WaiverClaimCreate,
    season_id: UUID = Query(..., description="Season for the waiver claim"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a waiver claim to pick up a free agent Pokemon."""
    logger.info(f"[WAIVER DEBUG] Creating claim: pokemon_id={claim.pokemon_id}, drop_pokemon_id={claim.drop_pokemon_id}, season_id={season_id}, user_id={current_user.id}")
    season = await fetch_season(season_id, db)

    logger.info(f"[WAIVER DEBUG] Season status: {season.status}")
    if season.status != SeasonStatus.ACTIVE:
        logger.error("[WAIVER DEBUG] Season not active")
        raise bad_request("Waiver claims can only be submitted during an active season")

    # Get league and check if waivers are enabled
    league_result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = league_result.scalar_one_or_none()

    if not league:
        logger.error("[WAIVER DEBUG] League not found")
        raise bad_request("League not found")

    waiver_enabled = league.settings.get(LeagueSettings.WAIVER_ENABLED, False)
    logger.info(f"[WAIVER DEBUG] Waiver enabled: {waiver_enabled}, league settings: {league.settings}")
    if not waiver_enabled:
        logger.error("[WAIVER DEBUG] Waiver wire not enabled")
        raise bad_request("Waiver wire is not enabled for this league")

    # Get user's team in this season
    team_result = await db.execute(
        select(TeamModel)
        .where(TeamModel.season_id == season_id)
        .where(TeamModel.user_id == current_user.id)
    )
    team = team_result.scalar_one_or_none()

    logger.info(f"[WAIVER DEBUG] Team found: {team}")
    if not team:
        logger.error("[WAIVER DEBUG] User has no team in season")
        raise forbidden("You don't have a team in this season")

    # Check if Pokemon is actually a free agent (not owned by any team in the season)
    owned_result = await db.execute(
        select(DraftPick)
        .join(TeamModel, DraftPick.team_id == TeamModel.id)
        .where(TeamModel.season_id == season_id)
        .where(DraftPick.pokemon_id == claim.pokemon_id)
    )
    owned_pokemon = owned_result.scalar_one_or_none()
    logger.info(f"[WAIVER DEBUG] Pokemon already owned: {owned_pokemon}")
    if owned_pokemon:
        logger.error("[WAIVER DEBUG] Pokemon already owned by a team")
        raise bad_request("This Pokemon is already owned by a team")

    # Check if user already has a pending claim for this Pokemon
    existing_claim_result = await db.execute(
        select(WaiverClaimModel)
        .where(WaiverClaimModel.team_id == team.id)
        .where(WaiverClaimModel.pokemon_id == claim.pokemon_id)
        .where(WaiverClaimModel.status == WaiverClaimStatus.PENDING)
    )
    existing_claim = existing_claim_result.scalar_one_or_none()
    logger.info(f"[WAIVER DEBUG] Existing pending claim: {existing_claim}")
    if existing_claim:
        logger.error("[WAIVER DEBUG] User already has pending claim for this Pokemon")
        raise bad_request("You already have a pending claim for this Pokemon")

    # Check weekly limit if configured
    max_per_week = league.settings.get(LeagueSettings.WAIVER_MAX_PER_WEEK)
    if max_per_week is not None:
        # Get current week number (you might want to calculate this from season start)
        current_week = season.settings.get(SeasonSettings.CURRENT_WEEK, 1)

        # Count claims this week
        week_claims_result = await db.execute(
            select(func.count(WaiverClaimModel.id))
            .where(WaiverClaimModel.team_id == team.id)
            .where(WaiverClaimModel.week_number == current_week)
            .where(WaiverClaimModel.status.in_([
                WaiverClaimStatus.PENDING,
                WaiverClaimStatus.APPROVED
            ]))
        )
        week_claims = week_claims_result.scalar() or 0

        if week_claims >= max_per_week:
            raise bad_request(f"You have reached the maximum of {max_per_week} waiver claims this week")

    # Check if drop is required based on roster size
    # Get the draft to find roster size limit
    from app.models.draft import Draft as DraftModel
    draft_result = await db.execute(
        select(DraftModel).where(DraftModel.season_id == season_id)
    )
    draft = draft_result.scalar_one_or_none()

    # Count current roster size (including pending approved claims)
    current_roster_result = await db.execute(
        select(func.count(DraftPick.id))
        .where(DraftPick.team_id == team.id)
    )
    current_roster_size = current_roster_result.scalar() or 0

    # Also count pending approved waiver claims that haven't been executed yet
    pending_approved_claims_result = await db.execute(
        select(func.count(WaiverClaimModel.id))
        .where(WaiverClaimModel.team_id == team.id)
        .where(WaiverClaimModel.status.in_([
            WaiverClaimStatus.PENDING,
            WaiverClaimStatus.APPROVED
        ]))
        .where(WaiverClaimModel.drop_pokemon_id.is_(None))
    )
    pending_adds = pending_approved_claims_result.scalar() or 0

    roster_size_limit = draft.roster_size if draft else 6  # Default to 6 if no draft found

    # Require drop if roster would exceed limit after this pickup
    require_drop = (current_roster_size + pending_adds) >= roster_size_limit

    # Also check the league setting for always requiring drops
    if league.settings.get(LeagueSettings.WAIVER_REQUIRE_DROP, False):
        require_drop = True

    logger.info(f"[WAIVER DEBUG] Roster size: {current_roster_size}, limit: {roster_size_limit}, pending_adds: {pending_adds}, require_drop: {require_drop}, drop_pokemon_id: {claim.drop_pokemon_id}")
    if require_drop and not claim.drop_pokemon_id:
        logger.error("[WAIVER DEBUG] Roster at capacity, drop required")
        raise bad_request(f"Your roster is at capacity ({current_roster_size}/{roster_size_limit}). You must specify a Pokemon to drop when making a waiver claim.")

    # Verify user owns the Pokemon they want to drop
    if claim.drop_pokemon_id:
        drop_result = await db.execute(
            select(DraftPick)
            .where(DraftPick.id == claim.drop_pokemon_id)
            .where(DraftPick.team_id == team.id)
        )
        if not drop_result.scalar_one_or_none():
            raise bad_request("You don't own the Pokemon you're trying to drop")

    # Determine approval requirements
    approval_type = league.settings.get(LeagueSettings.WAIVER_APPROVAL_TYPE, LeagueSettings.WAIVER_APPROVAL_NONE)
    requires_approval = approval_type != LeagueSettings.WAIVER_APPROVAL_NONE

    # Determine processing type
    processing_type_str = league.settings.get(LeagueSettings.WAIVER_PROCESSING_TYPE, LeagueSettings.WAIVER_PROCESSING_IMMEDIATE)
    processing_type = WaiverProcessingType(processing_type_str)

    # Calculate process_after for next_week processing
    process_after = None
    if processing_type == WaiverProcessingType.NEXT_WEEK:
        # This would typically be calculated based on your league's week schedule
        # For now, we'll leave it null and let a background job handle it
        pass

    # Get current week
    current_week = season.settings.get(SeasonSettings.CURRENT_WEEK, 1)

    # Calculate votes required for league vote
    votes_required = None
    if approval_type == LeagueSettings.WAIVER_APPROVAL_LEAGUE_VOTE:
        # Get number of league members
        member_count_result = await db.execute(
            select(func.count(LeagueMembership.id))
            .where(LeagueMembership.league_id == league.id)
            .where(LeagueMembership.is_active == True)
        )
        member_count = member_count_result.scalar() or 0
        # Require majority (more than half)
        votes_required = (member_count // 2) + 1

    db_claim = WaiverClaimModel(
        season_id=season_id,
        team_id=team.id,
        pokemon_id=claim.pokemon_id,
        drop_pokemon_id=claim.drop_pokemon_id,
        requires_approval=requires_approval,
        processing_type=processing_type,
        process_after=process_after,
        week_number=current_week,
        votes_required=votes_required,
    )
    db.add(db_claim)
    await db.commit()
    await db.refresh(db_claim)

    # If immediate processing and no approval needed, execute the claim
    if processing_type == WaiverProcessingType.IMMEDIATE and not requires_approval:
        await execute_waiver_claim(db_claim, db)
        db_claim.status = WaiverClaimStatus.APPROVED
        db_claim.resolved_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_claim)

    response = await build_waiver_claim_response(db_claim, db)

    # Broadcast the claim
    await waiver_manager.broadcast(season_id, {
        "event": "waiver_claim_created",
        "data": {"claim": response}
    })

    return response


@router.get("", response_model=WaiverClaimList)
async def list_waiver_claims(
    season_id: UUID = Query(..., description="Season to list claims for"),
    status_filter: str = Query(None, description="Filter by status"),
    team_id: UUID = Query(None, description="Filter by team"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List waiver claims in a season."""
    query = select(WaiverClaimModel).where(WaiverClaimModel.season_id == season_id)

    if status_filter:
        try:
            claim_status = WaiverClaimStatus(status_filter)
            query = query.where(WaiverClaimModel.status == claim_status)
        except ValueError:
            raise bad_request(f"Invalid status: {status_filter}")

    if team_id:
        query = query.where(WaiverClaimModel.team_id == team_id)

    result = await db.execute(query.order_by(WaiverClaimModel.created_at.desc()))
    claims = result.scalars().all()

    # Get pending count
    pending_result = await db.execute(
        select(func.count(WaiverClaimModel.id))
        .where(WaiverClaimModel.season_id == season_id)
        .where(WaiverClaimModel.status == WaiverClaimStatus.PENDING)
    )
    pending_count = pending_result.scalar() or 0

    return WaiverClaimList(
        claims=[await build_waiver_claim_response(claim, db) for claim in claims],
        total=len(claims),
        pending_count=pending_count,
    )


@router.get("/{claim_id}", response_model=WaiverClaimResponse)
async def get_waiver_claim(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get waiver claim details."""
    result = await db.execute(
        select(WaiverClaimModel).where(WaiverClaimModel.id == claim_id)
    )
    claim = result.scalar_one_or_none()

    if not claim:
        raise waiver_claim_not_found(claim_id)

    return await build_waiver_claim_response(claim, db)


@router.post("/{claim_id}/cancel", response_model=WaiverClaimResponse)
async def cancel_waiver_claim(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending waiver claim."""
    result = await db.execute(
        select(WaiverClaimModel).where(WaiverClaimModel.id == claim_id)
    )
    claim = result.scalar_one_or_none()

    if not claim:
        raise waiver_claim_not_found(claim_id)

    if claim.status != WaiverClaimStatus.PENDING:
        raise bad_request("Only pending claims can be cancelled")

    # Verify user owns the team
    team_result = await db.execute(
        select(TeamModel).where(TeamModel.id == claim.team_id)
    )
    team = team_result.scalar_one_or_none()

    if not team or team.user_id != current_user.id:
        raise forbidden("Only the claim owner can cancel this claim")

    claim.status = WaiverClaimStatus.CANCELLED
    claim.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(claim)

    response = await build_waiver_claim_response(claim, db)

    # Broadcast cancellation
    await waiver_manager.broadcast(claim.season_id, {
        "event": "waiver_claim_cancelled",
        "data": {"claim_id": str(claim_id)}
    })

    return response


@router.post("/{claim_id}/approve", response_model=WaiverClaimResponse)
async def admin_approve_claim(
    claim_id: UUID,
    action: WaiverAdminAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a waiver claim (league owner only)."""
    result = await db.execute(
        select(WaiverClaimModel).where(WaiverClaimModel.id == claim_id)
    )
    claim = result.scalar_one_or_none()

    if not claim:
        raise waiver_claim_not_found(claim_id)

    if claim.status != WaiverClaimStatus.PENDING:
        raise bad_request("Only pending claims can be approved/rejected")

    if not claim.requires_approval:
        raise bad_request("This claim does not require approval")

    # Get season and verify user is league owner
    season_result = await db.execute(
        select(SeasonModel).where(SeasonModel.id == claim.season_id)
    )
    season = season_result.scalar_one_or_none()

    league_result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = league_result.scalar_one_or_none()

    # Check if this is admin approval type
    approval_type = league.settings.get(LeagueSettings.WAIVER_APPROVAL_TYPE, LeagueSettings.WAIVER_APPROVAL_NONE)
    if approval_type != LeagueSettings.WAIVER_APPROVAL_ADMIN:
        raise bad_request("This league uses league vote approval, not admin approval")

    if not league or league.owner_id != current_user.id:
        raise not_league_owner()

    if action.approved:
        # Execute the claim
        await execute_waiver_claim(claim, db)
        claim.status = WaiverClaimStatus.APPROVED
        claim.admin_approved = True
    else:
        claim.status = WaiverClaimStatus.REJECTED
        claim.admin_approved = False

    claim.admin_notes = action.notes
    claim.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(claim)

    response = await build_waiver_claim_response(claim, db)

    # Broadcast result
    event = "waiver_claim_approved" if action.approved else "waiver_claim_rejected"
    await waiver_manager.broadcast(claim.season_id, {
        "event": event,
        "data": {"claim": response}
    })

    return response


@router.post("/{claim_id}/vote", response_model=WaiverVoteResponse)
async def vote_on_claim(
    claim_id: UUID,
    vote: WaiverVoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Vote on a waiver claim (for league vote approval)."""
    result = await db.execute(
        select(WaiverClaimModel).where(WaiverClaimModel.id == claim_id)
    )
    claim = result.scalar_one_or_none()

    if not claim:
        raise waiver_claim_not_found(claim_id)

    if claim.status != WaiverClaimStatus.PENDING:
        raise bad_request("Voting is only allowed on pending claims")

    # Get league to verify approval type
    season_result = await db.execute(
        select(SeasonModel).where(SeasonModel.id == claim.season_id)
    )
    season = season_result.scalar_one_or_none()

    league_result = await db.execute(
        select(LeagueModel).where(LeagueModel.id == season.league_id)
    )
    league = league_result.scalar_one_or_none()

    approval_type = league.settings.get(LeagueSettings.WAIVER_APPROVAL_TYPE, LeagueSettings.WAIVER_APPROVAL_NONE)
    if approval_type != LeagueSettings.WAIVER_APPROVAL_LEAGUE_VOTE:
        raise bad_request("This league does not use league vote approval")

    # Verify user is a league member
    membership_result = await db.execute(
        select(LeagueMembership)
        .where(LeagueMembership.league_id == league.id)
        .where(LeagueMembership.user_id == current_user.id)
        .where(LeagueMembership.is_active == True)
    )
    if not membership_result.scalar_one_or_none():
        raise forbidden("You are not a member of this league")

    # Check if user already voted
    existing_vote_result = await db.execute(
        select(WaiverVoteModel)
        .where(WaiverVoteModel.waiver_claim_id == claim_id)
        .where(WaiverVoteModel.user_id == current_user.id)
    )
    existing_vote = existing_vote_result.scalar_one_or_none()

    if existing_vote:
        # Update existing vote
        existing_vote.vote = vote.vote
        db_vote = existing_vote
    else:
        # Create new vote
        db_vote = WaiverVoteModel(
            waiver_claim_id=claim_id,
            user_id=current_user.id,
            vote=vote.vote,
        )
        db.add(db_vote)

    # Update vote counts
    if vote.vote:
        if not existing_vote or not existing_vote.vote:
            claim.votes_for += 1
            if existing_vote and not existing_vote.vote:
                claim.votes_against -= 1
    else:
        if not existing_vote or existing_vote.vote:
            claim.votes_against += 1
            if existing_vote and existing_vote.vote:
                claim.votes_for -= 1

    await db.flush()
    await db.refresh(db_vote)

    # Check if votes threshold is met
    if claim.votes_required and claim.votes_for >= claim.votes_required:
        # Execute the claim
        await execute_waiver_claim(claim, db)
        claim.status = WaiverClaimStatus.APPROVED
        claim.resolved_at = datetime.utcnow()

        # Broadcast approval
        response = await build_waiver_claim_response(claim, db)
        await waiver_manager.broadcast(claim.season_id, {
            "event": "waiver_claim_approved",
            "data": {"claim": response}
        })

    await db.commit()
    await db.refresh(db_vote)

    # Broadcast vote update
    await waiver_manager.broadcast(claim.season_id, {
        "event": "waiver_vote_cast",
        "data": {
            "claim_id": str(claim_id),
            "votes_for": claim.votes_for,
            "votes_against": claim.votes_against,
        }
    })

    return WaiverVoteResponse(
        id=db_vote.id,
        waiver_claim_id=db_vote.waiver_claim_id,
        user_id=db_vote.user_id,
        vote=db_vote.vote,
        created_at=db_vote.created_at,
    )


@router.get("/free-agents/", response_model=FreeAgentList)
async def list_free_agents(
    season_id: UUID = Query(..., description="Season to list free agents for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List Pokemon available as free agents in a season."""
    from app.models.pokemon import Pokemon as PokemonModel
    from app.services.pokeapi import pokeapi_service

    season = await fetch_season(season_id, db)

    # Get draft pool for the season
    from app.models.draft import Draft as DraftModel
    draft_result = await db.execute(
        select(DraftModel).where(DraftModel.season_id == season_id)
    )
    draft = draft_result.scalar_one_or_none()

    if not draft:
        return FreeAgentList(pokemon=[], total=0)

    # Extract pokemon IDs from the pokemon_pool dictionary keys
    # pokemon_pool is stored as {"1": {...}, "4": {...}, etc}
    pool_pokemon_ids = [int(pid) for pid in draft.pokemon_pool.keys()] if draft.pokemon_pool else []
    if not pool_pokemon_ids:
        return FreeAgentList(pokemon=[], total=0)

    # Get Pokemon that are owned by teams in this season
    owned_result = await db.execute(
        select(DraftPick.pokemon_id)
        .join(TeamModel, DraftPick.team_id == TeamModel.id)
        .where(TeamModel.season_id == season_id)
    )
    owned_pokemon_ids = {row[0] for row in owned_result.all()}

    # Free agents are in the pool but not owned
    free_agent_ids = [pid for pid in pool_pokemon_ids if pid not in owned_pokemon_ids]

    if not free_agent_ids:
        return FreeAgentList(pokemon=[], total=0)

    # Get Pokemon data
    pokemon_data_map = await pokeapi_service.get_pokemon_batch(free_agent_ids, db)

    free_agents = []
    for pokemon_id in free_agent_ids:
        pokemon_data = pokemon_data_map.get(pokemon_id)
        if pokemon_data:
            free_agents.append(FreeAgentPokemon(
                pokemon_id=pokemon_id,
                name=pokemon_data.get("name", "Unknown"),
                types=pokemon_data.get("types", []),
                sprite=pokemon_data.get("sprite"),
                base_stat_total=pokemon_data.get("base_stat_total"),
                generation=pokemon_data.get("generation"),
            ))

    return FreeAgentList(pokemon=free_agents, total=len(free_agents))


async def execute_waiver_claim(claim: WaiverClaimModel, db: AsyncSession):
    """
    Execute a waiver claim - add Pokemon to team and optionally drop another.

    This function creates a new DraftPick for the claimed Pokemon and
    removes the dropped Pokemon from the team if specified.
    """
    from app.models.team import AcquisitionType

    # Get the draft for this season to link the pick
    from app.models.draft import Draft as DraftModel
    draft_result = await db.execute(
        select(DraftModel)
        .join(SeasonModel, DraftModel.season_id == SeasonModel.id)
        .where(SeasonModel.id == claim.season_id)
    )
    draft = draft_result.scalar_one_or_none()

    if not draft:
        raise bad_request("No draft found for this season")

    # If dropping a Pokemon, remove it from the team
    if claim.drop_pokemon_id:
        drop_result = await db.execute(
            select(DraftPick).where(DraftPick.id == claim.drop_pokemon_id)
        )
        drop_pick = drop_result.scalar_one_or_none()
        if drop_pick:
            # Remove the pick (Pokemon goes back to free agent pool)
            await db.delete(drop_pick)

    # Get max pick number for ordering
    max_pick_result = await db.execute(
        select(func.max(DraftPick.pick_number)).where(DraftPick.draft_id == draft.id)
    )
    max_pick = max_pick_result.scalar() or 0

    # Create new draft pick for the claimed Pokemon
    new_pick = DraftPick(
        draft_id=draft.id,
        team_id=claim.team_id,
        pokemon_id=claim.pokemon_id,
        pick_number=max_pick + 1,
        # Note: acquisition_type would need to be added to DraftPick model
        # For now, we just track it via the waiver claim
    )
    db.add(new_pick)
