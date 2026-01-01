"""
Integration tests for Waiver Wire / Free Agent requirements (FR-WAIVER-*).

These tests verify waiver claim creation, approval workflows, and free agent management
as specified in the requirements document.
"""

import pytest
from datetime import datetime
from sqlalchemy import select

from app.models import Draft, Team, DraftPick, WaiverClaim
from app.models.waiver import WaiverClaimStatus, WaiverProcessingType
from app.models.season import SeasonStatus
from tests.utils.factories import (
    DraftFactory,
    SeasonFactory,
    TeamFactory,
    PokemonFactory,
    LeagueFactory,
    UserFactory,
    WaiverClaimFactory,
)
from tests.utils.helpers import count_records, exists


# ============================================================================
# FR-WAIVER-001: Waiver claim creation
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
async def test_create_waiver_claim(db_session):
    """
    Test FR-WAIVER-001: The system shall allow teams to submit waiver claims
    for free agent Pokemon.

    Scenario:
        1. Create season with team
        2. Create waiver claim for a free agent Pokemon
        3. Verify claim created with correct status
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(
        db_session,
        season_id=season.id,
        pokemon_pool={"pool": [25, 1, 4, 7]},  # Pikachu, Bulbasaur, Charmander, Squirtle
    )
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    # Act
    claim = await WaiverClaimFactory.create_for_season(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,  # Pikachu
    )

    # Assert
    assert claim.id is not None
    assert claim.season_id == season.id
    assert claim.team_id == team.id
    assert claim.pokemon_id == 25
    assert claim.status == WaiverClaimStatus.PENDING


@pytest.mark.waiver
@pytest.mark.integration
async def test_waiver_claim_with_drop(db_session):
    """
    Test FR-WAIVER-002: The system shall allow teams to specify a Pokemon to drop
    when submitting a waiver claim.

    Scenario:
        1. Create team with an existing Pokemon
        2. Create waiver claim with a drop Pokemon specified
        3. Verify drop Pokemon is recorded
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(
        db_session,
        season_id=season.id,
        pokemon_pool={"pool": [25, 1, 4, 7]},
    )
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    # Create an existing Pokemon on the team
    existing_pick = DraftPick(
        draft_id=draft.id,
        team_id=team.id,
        pokemon_id=1,  # Bulbasaur
        pick_number=1,
    )
    db_session.add(existing_pick)
    await db_session.flush()
    await db_session.refresh(existing_pick)

    # Act
    claim = await WaiverClaimFactory.create_for_season(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,  # Claim Pikachu
        drop_pokemon_id=existing_pick.id,  # Drop Bulbasaur
    )

    # Assert
    assert claim.drop_pokemon_id == existing_pick.id


# ============================================================================
# FR-WAIVER-003 & FR-WAIVER-004: Approval workflows
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
async def test_waiver_claim_requires_admin_approval(db_session):
    """
    Test FR-WAIVER-003: The system shall support admin approval for waiver claims
    when configured in league settings.

    Scenario:
        1. Create claim requiring approval
        2. Verify requires_approval flag is set
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    # Act
    claim = await WaiverClaimFactory.create_with_approval(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
        approval_type="admin",
    )

    # Assert
    assert claim.requires_approval is True
    assert claim.status == WaiverClaimStatus.PENDING


@pytest.mark.waiver
@pytest.mark.integration
async def test_waiver_claim_league_vote_approval(db_session):
    """
    Test FR-WAIVER-004: The system shall support league vote approval for waiver claims.

    Scenario:
        1. Create claim requiring league vote
        2. Verify votes_required is set
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    # Act
    claim = await WaiverClaimFactory.create_with_approval(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
        approval_type="league_vote",
        votes_required=3,
    )

    # Assert
    assert claim.requires_approval is True
    assert claim.votes_required == 3
    assert claim.votes_for == 0
    assert claim.votes_against == 0


# ============================================================================
# FR-WAIVER-005 & FR-WAIVER-006: Processing timing
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
@pytest.mark.parametrize(
    "processing_type",
    [WaiverProcessingType.IMMEDIATE, WaiverProcessingType.NEXT_WEEK],
)
async def test_waiver_processing_types(db_session, processing_type):
    """
    Test FR-WAIVER-005 & FR-WAIVER-006: The system shall support immediate
    and next-week processing for waiver claims.

    Scenario:
        1. Create claims with different processing types
        2. Verify processing type is stored correctly
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    # Act
    claim = await WaiverClaimFactory.create_for_season(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
        processing_type=processing_type,
    )

    # Assert
    assert claim.processing_type == processing_type


# ============================================================================
# FR-WAIVER-007: Weekly limits
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
async def test_waiver_claim_week_tracking(db_session):
    """
    Test FR-WAIVER-007: The system shall track waiver claims by week number.

    Scenario:
        1. Create claims with week number
        2. Verify week tracking
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    # Act
    claim = await WaiverClaimFactory.create_for_season(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
        week_number=3,
    )

    # Assert
    assert claim.week_number == 3


# ============================================================================
# FR-WAIVER-008: Claim status transitions
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
@pytest.mark.parametrize(
    "status",
    [
        WaiverClaimStatus.PENDING,
        WaiverClaimStatus.APPROVED,
        WaiverClaimStatus.REJECTED,
        WaiverClaimStatus.CANCELLED,
        WaiverClaimStatus.EXPIRED,
    ],
)
async def test_waiver_claim_status_values(db_session, status):
    """
    Test FR-WAIVER-008: The system shall track waiver claim status through
    states: pending, approved, rejected, cancelled, expired.

    Scenario:
        1. Create claims with various statuses
        2. Verify status stored correctly
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    # Act
    claim = await WaiverClaimFactory.create_for_season(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
        status=status,
    )

    # Assert
    assert claim.status == status


# ============================================================================
# FR-WAIVER-009: Cancellation
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
async def test_cancel_pending_waiver_claim(db_session):
    """
    Test FR-WAIVER-009: The system shall allow teams to cancel pending waiver claims.

    Scenario:
        1. Create pending claim
        2. Update status to cancelled
        3. Verify resolved_at is set
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    claim = await WaiverClaimFactory.create_for_season(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
    )

    # Act
    claim.status = WaiverClaimStatus.CANCELLED
    claim.resolved_at = datetime.utcnow()
    await db_session.commit()
    await db_session.refresh(claim)

    # Assert
    assert claim.status == WaiverClaimStatus.CANCELLED
    assert claim.resolved_at is not None


# ============================================================================
# FR-WAIVER-010: Admin approval
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
async def test_admin_approve_waiver_claim(db_session):
    """
    Test FR-WAIVER-010: The system shall allow league owners to approve
    waiver claims awaiting admin approval.

    Scenario:
        1. Create claim requiring admin approval
        2. Approve the claim
        3. Verify admin_approved and resolved_at are set
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    claim = await WaiverClaimFactory.create_with_approval(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
        approval_type="admin",
    )

    # Act
    claim.status = WaiverClaimStatus.APPROVED
    claim.admin_approved = True
    claim.admin_notes = "Looks good!"
    claim.resolved_at = datetime.utcnow()
    await db_session.commit()
    await db_session.refresh(claim)

    # Assert
    assert claim.status == WaiverClaimStatus.APPROVED
    assert claim.admin_approved is True
    assert claim.admin_notes == "Looks good!"
    assert claim.resolved_at is not None


@pytest.mark.waiver
@pytest.mark.integration
async def test_admin_reject_waiver_claim(db_session):
    """
    Test FR-WAIVER-011: The system shall allow league owners to reject
    waiver claims awaiting admin approval.

    Scenario:
        1. Create claim requiring admin approval
        2. Reject the claim
        3. Verify admin_approved is False and status is rejected
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    claim = await WaiverClaimFactory.create_with_approval(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
        approval_type="admin",
    )

    # Act
    claim.status = WaiverClaimStatus.REJECTED
    claim.admin_approved = False
    claim.admin_notes = "This pickup would unbalance the league."
    claim.resolved_at = datetime.utcnow()
    await db_session.commit()
    await db_session.refresh(claim)

    # Assert
    assert claim.status == WaiverClaimStatus.REJECTED
    assert claim.admin_approved is False
    assert claim.admin_notes == "This pickup would unbalance the league."


# ============================================================================
# FR-WAIVER-012: Vote tracking
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
async def test_waiver_vote_tracking(db_session):
    """
    Test FR-WAIVER-012: The system shall track votes for league vote approval.

    Scenario:
        1. Create claim requiring league vote
        2. Update vote counts
        3. Verify vote totals
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    claim = await WaiverClaimFactory.create_with_approval(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
        approval_type="league_vote",
        votes_required=3,
    )

    # Act - Simulate voting
    claim.votes_for = 2
    claim.votes_against = 1
    await db_session.commit()
    await db_session.refresh(claim)

    # Assert
    assert claim.votes_for == 2
    assert claim.votes_against == 1
    assert claim.votes_required == 3


@pytest.mark.waiver
@pytest.mark.integration
async def test_waiver_claim_approved_by_votes(db_session):
    """
    Test FR-WAIVER-013: The system shall automatically approve claims when
    vote threshold is met.

    Scenario:
        1. Create claim requiring 3 votes
        2. Add enough votes to reach threshold
        3. Approve the claim
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session,
        season_id=season.id,
        draft_id=draft.id,
        user_id=user.id,
    )

    claim = await WaiverClaimFactory.create_with_approval(
        db_session,
        season=season,
        team=team,
        pokemon_id=25,
        approval_type="league_vote",
        votes_required=3,
    )

    # Act - Reach vote threshold
    claim.votes_for = 3
    if claim.votes_for >= claim.votes_required:
        claim.status = WaiverClaimStatus.APPROVED
        claim.resolved_at = datetime.utcnow()

    await db_session.commit()
    await db_session.refresh(claim)

    # Assert
    assert claim.votes_for >= claim.votes_required
    assert claim.status == WaiverClaimStatus.APPROVED


# ============================================================================
# FR-WAIVER-014: Priority ordering
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
async def test_waiver_claim_priority(db_session):
    """
    Test FR-WAIVER-014: The system shall track priority for waiver claims.

    Scenario:
        1. Create multiple claims with different priorities
        2. Verify priorities are stored correctly
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)

    teams = []
    for i in range(3):
        user = await UserFactory.create(db_session)
        team = await TeamFactory.create(
            db_session,
            season_id=season.id,
            draft_id=draft.id,
            user_id=user.id,
        )
        teams.append(team)

    # Act - Create claims with different priorities
    claims = []
    for i, team in enumerate(teams):
        claim = await WaiverClaimFactory.create_for_season(
            db_session,
            season=season,
            team=team,
            pokemon_id=25,
            priority=i + 1,
        )
        claims.append(claim)

    # Assert
    assert claims[0].priority == 1
    assert claims[1].priority == 2
    assert claims[2].priority == 3


# ============================================================================
# Batch and query tests
# ============================================================================


@pytest.mark.waiver
@pytest.mark.integration
async def test_list_waiver_claims_by_season(db_session):
    """
    Test listing waiver claims filtered by season.

    Scenario:
        1. Create claims in multiple seasons
        2. Query by season
        3. Verify only relevant claims returned
    """
    # Arrange
    season1 = await SeasonFactory.create_with_league(db_session, status="active")
    season2 = await SeasonFactory.create_with_league(db_session, status="active")

    draft1 = await DraftFactory.create(db_session, season_id=season1.id)
    draft2 = await DraftFactory.create(db_session, season_id=season2.id)

    user = await UserFactory.create(db_session)
    team1 = await TeamFactory.create(
        db_session, season_id=season1.id, draft_id=draft1.id, user_id=user.id
    )
    team2 = await TeamFactory.create(
        db_session, season_id=season2.id, draft_id=draft2.id, user_id=user.id
    )

    # Create 2 claims in season1, 1 in season2
    await WaiverClaimFactory.create_for_season(db_session, season=season1, team=team1, pokemon_id=25)
    await WaiverClaimFactory.create_for_season(db_session, season=season1, team=team1, pokemon_id=1)
    await WaiverClaimFactory.create_for_season(db_session, season=season2, team=team2, pokemon_id=4)

    # Act
    result = await db_session.execute(
        select(WaiverClaim).where(WaiverClaim.season_id == season1.id)
    )
    season1_claims = result.scalars().all()

    # Assert
    assert len(season1_claims) == 2


@pytest.mark.waiver
@pytest.mark.integration
async def test_list_waiver_claims_by_status(db_session):
    """
    Test listing waiver claims filtered by status.

    Scenario:
        1. Create claims with different statuses
        2. Query by status
        3. Verify filtering works
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session, status="active")
    draft = await DraftFactory.create(db_session, season_id=season.id)
    user = await UserFactory.create(db_session)
    team = await TeamFactory.create(
        db_session, season_id=season.id, draft_id=draft.id, user_id=user.id
    )

    await WaiverClaimFactory.create_for_season(
        db_session, season=season, team=team, pokemon_id=25, status=WaiverClaimStatus.PENDING
    )
    await WaiverClaimFactory.create_for_season(
        db_session, season=season, team=team, pokemon_id=1, status=WaiverClaimStatus.APPROVED
    )
    await WaiverClaimFactory.create_for_season(
        db_session, season=season, team=team, pokemon_id=4, status=WaiverClaimStatus.PENDING
    )

    # Act
    result = await db_session.execute(
        select(WaiverClaim)
        .where(WaiverClaim.season_id == season.id)
        .where(WaiverClaim.status == WaiverClaimStatus.PENDING)
    )
    pending_claims = result.scalars().all()

    # Assert
    assert len(pending_claims) == 2
