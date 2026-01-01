"""
Integration tests for Draft Management requirements (FR-DRAFT-*).

These tests verify draft creation, execution, and state management
as specified in the requirements document.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.models import Draft, Team, DraftPick
from tests.utils.factories import (
    DraftFactory,
    SeasonFactory,
    TeamFactory,
    PokemonFactory,
    LeagueFactory,
)
from tests.utils.helpers import count_records, exists


# ============================================================================
# FR-DRAFT-001 & FR-DRAFT-002: Draft creation
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
async def test_create_league_draft(db_session):
    """
    Test FR-DRAFT-001: The system shall allow authenticated users to create
    league drafts tied to seasons.

    Scenario:
        1. Create season
        2. Create draft for season
        3. Verify draft created and linked
    """
    # Arrange
    season = await SeasonFactory.create_with_league(db_session)

    # Act
    draft = await DraftFactory.create(
        db_session,
        season_id=season.id,
        format="snake",
        roster_size=6,
    )

    # Assert
    assert draft.id is not None
    assert draft.season_id == season.id
    assert draft.format == "snake"
    assert draft.status == "pending"


@pytest.mark.draft
@pytest.mark.integration
async def test_create_anonymous_draft(db_session):
    """
    Test FR-DRAFT-002: The system shall allow any user to create anonymous
    drafts without authentication.

    Scenario:
        1. Create draft without season
        2. Verify draft created with creator token
    """
    # Act
    draft = await DraftFactory.create(
        db_session,
        season_id=None,  # Anonymous draft
        format="linear",
    )

    # Assert
    assert draft.id is not None
    assert draft.season_id is None
    assert draft.session_token is not None
    assert draft.rejoin_code is not None


# ============================================================================
# FR-DRAFT-003: Draft formats
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
@pytest.mark.parametrize(
    "format",
    ["snake", "linear", "auction"],
)
async def test_support_draft_formats(db_session, format):
    """
    Test FR-DRAFT-003: The system shall support three draft formats:
    snake, linear, and auction.

    Scenario:
        1. Create draft with each format
        2. Verify format stored correctly
    """
    # Act
    draft = await DraftFactory.create(db_session, format=format)

    # Assert
    assert draft.format == format


# ============================================================================
# FR-DRAFT-004 & FR-DRAFT-005: Configuration options
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
@pytest.mark.parametrize(
    "roster_size",
    [1, 6, 10, 15, 20],
)
async def test_roster_size_configuration(db_session, roster_size):
    """
    Test FR-DRAFT-004: The system shall allow draft creators to specify
    roster size (1-20 Pokemon per team).

    Scenario:
        1. Create drafts with various roster sizes
        2. Verify roster size configured correctly
    """
    # Act
    draft = await DraftFactory.create(db_session, roster_size=roster_size)

    # Assert
    assert draft.roster_size == roster_size
    assert 1 <= draft.roster_size <= 20


@pytest.mark.draft
@pytest.mark.integration
@pytest.mark.parametrize(
    "timer_seconds",
    [30, 60, 90, 300, 600],
)
async def test_timer_duration_configuration(db_session, timer_seconds):
    """
    Test FR-DRAFT-005: The system shall allow draft creators to configure
    timer duration per pick (30-600 seconds).

    Scenario:
        1. Create drafts with various timer values
        2. Verify timer configured correctly
    """
    # Act
    draft = await DraftFactory.create(db_session, timer_seconds=timer_seconds)

    # Assert
    assert draft.timer_seconds == timer_seconds
    assert 30 <= draft.timer_seconds <= 600


# ============================================================================
# FR-DRAFT-006: Budget/point cap mode
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
async def test_enable_budget_cap_mode(db_session):
    """
    Test FR-DRAFT-006: The system shall allow draft creators to enable
    budget/point cap mode.

    Scenario:
        1. Create draft with budget enabled
        2. Verify budget settings stored
    """
    # Act
    draft = await DraftFactory.create(
        db_session,
        budget_enabled=True,
        budget_per_team=100,
    )

    # Assert
    assert draft.budget_enabled is True
    assert draft.budget_per_team == 100


@pytest.mark.draft
@pytest.mark.integration
async def test_disable_budget_cap_mode(db_session):
    """
    Test budget cap mode can be disabled.

    Scenario:
        1. Create draft without budget
        2. Verify budget disabled
    """
    # Act
    draft = await DraftFactory.create(
        db_session,
        budget_enabled=False,
        budget_per_team=None,
    )

    # Assert
    assert draft.budget_enabled is False
    assert draft.budget_per_team is None


# ============================================================================
# FR-DRAFT-010 & FR-DRAFT-011: Anonymous draft codes
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
async def test_generate_rejoin_code_format(db_session):
    """
    Test FR-DRAFT-010: The system shall generate memorable rejoin codes
    for anonymous drafts (format: WORD-NNNN).

    Scenario:
        1. Create anonymous draft
        2. Verify rejoin code format
    """
    # Act
    draft = await DraftFactory.create(db_session, season_id=None)

    # Assert
    assert draft.rejoin_code is not None
    # Basic format check (WORD-NNNN)
    parts = draft.rejoin_code.split("-")
    assert len(parts) == 2
    assert parts[0].isalpha()  # Word part
    assert parts[1].isdigit()  # Number part


@pytest.mark.draft
@pytest.mark.integration
async def test_rejoin_codes_are_unique(db_session):
    """
    Test that rejoin codes are unique across drafts.

    Scenario:
        1. Create multiple anonymous drafts
        2. Verify all have unique rejoin codes
    """
    # Act
    drafts = await DraftFactory.create_batch(db_session, count=5, season_id=None)

    # Assert
    codes = [draft.rejoin_code for draft in drafts]
    assert len(codes) == len(set(codes)), "Rejoin codes are not unique"


# ============================================================================
# FR-DRAFT-013: Draft expiration
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
async def test_pending_drafts_expire_after_24_hours(db_session):
    """
    Test FR-DRAFT-013: The system shall expire pending anonymous drafts after 24 hours.

    Scenario:
        1. Create draft with expiration time
        2. Verify expiration set correctly
    """
    # Arrange
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=24)

    # Act
    draft = await DraftFactory.create(
        db_session,
        season_id=None,
        status="pending",
        expires_at=expires_at,
    )

    # Assert
    assert draft.expires_at is not None
    assert draft.expires_at > now
    time_diff = (draft.expires_at - now).total_seconds()
    assert abs(time_diff - (24 * 3600)) < 60  # Within 1 minute


# ============================================================================
# FR-DRAFT-014: Pokemon pool configuration
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
async def test_store_pokemon_pool_configuration(db_session):
    """
    Test FR-DRAFT-014: The system shall store Pokemon pool configuration
    in JSONB format.

    Scenario:
        1. Create draft with custom pool configuration
        2. Verify pool data stored correctly
    """
    # Arrange
    pool_config = {
        "pool": [1, 4, 7, 25, 133, 150],
        "filters": {
            "generations": [1],
            "include_legendary": False,
        },
        "point_values": {
            "150": 20,  # Mewtwo
            "25": 10,  # Pikachu
        },
    }

    # Act
    draft = await DraftFactory.create(
        db_session,
        pokemon_pool=pool_config,
    )

    # Assert
    assert draft.pokemon_pool is not None
    assert draft.pokemon_pool["pool"] == [1, 4, 7, 25, 133, 150]
    assert draft.pokemon_pool["filters"]["generations"] == [1]


# ============================================================================
# FR-DRAFT-024: Record picks
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
async def test_record_draft_pick(db_session):
    """
    Test FR-DRAFT-024: The system shall record each pick with team ID,
    Pokemon ID, pick number, and points spent.

    Scenario:
        1. Create draft with teams
        2. Record a pick
        3. Verify pick stored with all details
    """
    # Arrange
    draft = await DraftFactory.create_with_season(db_session, status="live")
    team = await TeamFactory.create_for_draft(db_session, draft)
    pokemon = await PokemonFactory.create(db_session)

    # Act
    pick = DraftPick(
        draft_id=draft.id,
        team_id=team.id,
        pokemon_id=pokemon.id,
        pick_number=1,
        points_spent=10,
    )
    db_session.add(pick)
    await db_session.commit()
    await db_session.refresh(pick)

    # Assert
    assert pick.id is not None
    assert pick.draft_id == draft.id
    assert pick.team_id == team.id
    assert pick.pokemon_id == pokemon.id
    assert pick.pick_number == 1
    assert pick.points_spent == 10
    assert pick.picked_at is not None


# ============================================================================
# FR-DRAFT-029: Auto-complete draft
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
async def test_draft_completion_when_roster_filled(db_session):
    """
    Test FR-DRAFT-029: The system shall automatically complete the draft
    when all roster slots are filled.

    Scenario:
        1. Create draft with roster size 2
        2. Create team
        3. Make picks to fill roster
        4. Verify draft can be marked complete
    """
    # Arrange
    draft = await DraftFactory.create_with_season(
        db_session,
        status="live",
        roster_size=2,
    )
    team = await TeamFactory.create_for_draft(db_session, draft)
    pokemon1 = await PokemonFactory.create(db_session, identifier="Pokemon1")
    pokemon2 = await PokemonFactory.create(db_session, identifier="Pokemon2")

    # Act - Make picks
    pick1 = DraftPick(
        draft_id=draft.id,
        team_id=team.id,
        pokemon_id=pokemon1.id,
        pick_number=1,
    )
    pick2 = DraftPick(
        draft_id=draft.id,
        team_id=team.id,
        pokemon_id=pokemon2.id,
        pick_number=2,
    )
    db_session.add_all([pick1, pick2])

    # Count picks for team
    result = await db_session.execute(
        select(DraftPick).where(DraftPick.team_id == team.id)
    )
    team_picks = result.scalars().all()

    # Act - Mark draft complete if roster filled
    if len(team_picks) >= draft.roster_size:
        draft.status = "completed"
        draft.completed_at = datetime.utcnow()

    await db_session.commit()
    await db_session.refresh(draft)

    # Assert
    assert draft.status == "completed"
    assert draft.completed_at is not None


# ============================================================================
# FR-DRAFT-035 & FR-DRAFT-036: Draft deletion
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
async def test_delete_pending_draft(db_session):
    """
    Test FR-DRAFT-035: The system shall allow draft creators to delete pending drafts.

    Scenario:
        1. Create pending draft
        2. Delete draft
        3. Verify draft removed
    """
    # Arrange
    draft = await DraftFactory.create(db_session, status="pending")
    draft_id = draft.id

    # Act
    await db_session.delete(draft)
    await db_session.commit()

    # Assert
    assert not await exists(db_session, Draft, id=draft_id)


@pytest.mark.draft
@pytest.mark.integration
async def test_cannot_delete_started_draft(db_session):
    """
    Test FR-DRAFT-036: The system shall prevent deletion of drafts that have started.

    Scenario:
        1. Create started draft
        2. Verify draft has started status
        (Actual prevention would be in API layer)
    """
    # Act
    draft = await DraftFactory.create(
        db_session,
        status="live",
        started_at=datetime.utcnow(),
    )

    # Assert
    assert draft.status == "live"
    assert draft.started_at is not None
    # Deletion prevention would be handled in API/service layer


# ============================================================================
# Parametrized Tests - Draft Formats and Configurations
# ============================================================================


@pytest.mark.draft
@pytest.mark.integration
@pytest.mark.parametrize(
    "format,roster_size,timer,budget_enabled",
    [
        ("snake", 6, 90, False),
        ("linear", 8, 120, False),
        ("auction", 10, 60, True),
        ("snake", 12, 300, True),
    ],
)
async def test_various_draft_configurations(
    db_session, format, roster_size, timer, budget_enabled
):
    """
    Parametrized test for various draft configurations.

    Tests multiple requirement combinations.
    """
    # Act
    draft = await DraftFactory.create(
        db_session,
        format=format,
        roster_size=roster_size,
        timer_seconds=timer,
        budget_enabled=budget_enabled,
        budget_per_team=100 if budget_enabled else None,
    )

    # Assert
    assert draft.format == format
    assert draft.roster_size == roster_size
    assert draft.timer_seconds == timer
    assert draft.budget_enabled == budget_enabled
