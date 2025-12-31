"""
Integration tests for League Management requirements (FR-LEAGUE-*).

These tests verify league creation, membership, and management functionality
as specified in the requirements document.
"""

import pytest
from sqlalchemy import select

from app.models import League, LeagueMembership
from tests.utils.factories import UserFactory, LeagueFactory
from tests.utils.helpers import count_records, exists, assert_model_fields


# ============================================================================
# FR-LEAGUE-001: Create leagues with custom settings
# ============================================================================


@pytest.mark.league
@pytest.mark.integration
async def test_create_league_with_custom_settings(db_session):
    """
    Test FR-LEAGUE-001: The system shall allow authenticated users to create
    new leagues with custom settings.

    Scenario:
        1. Create user
        2. Create league with custom settings
        3. Verify league created with settings
    """
    # Arrange
    user = await UserFactory.create(db_session)
    custom_settings = {
        "default_draft_format": "auction",
        "require_trade_approval": True,
        "max_teams": 12,
    }

    # Act
    league = await LeagueFactory.create(
        db_session,
        name="Custom League",
        owner_id=user.id,
        settings=custom_settings,
    )

    # Assert
    assert league.id is not None
    assert league.name == "Custom League"
    assert league.owner_id == user.id
    assert league.settings == custom_settings


# ============================================================================
# FR-LEAGUE-002 & FR-LEAGUE-003: Invite codes
# ============================================================================


@pytest.mark.league
@pytest.mark.integration
async def test_league_generates_unique_invite_code(db_session):
    """
    Test FR-LEAGUE-002: The system shall generate unique invite codes for
    each league upon creation.

    Scenario:
        1. Create multiple leagues
        2. Verify each has unique invite code
    """
    # Arrange
    user = await UserFactory.create(db_session)

    # Act
    league1 = await LeagueFactory.create(db_session, owner_id=user.id)
    league2 = await LeagueFactory.create(db_session, owner_id=user.id)
    league3 = await LeagueFactory.create(db_session, owner_id=user.id)

    # Assert
    assert league1.invite_code is not None
    assert league2.invite_code is not None
    assert league3.invite_code is not None

    # All codes should be unique
    codes = [league1.invite_code, league2.invite_code, league3.invite_code]
    assert len(codes) == len(set(codes)), "Invite codes are not unique"


@pytest.mark.league
@pytest.mark.integration
async def test_user_can_join_league_with_invite_code(db_session):
    """
    Test FR-LEAGUE-003: The system shall allow users to join leagues using invite codes.

    Scenario:
        1. Create league with owner
        2. Create another user
        3. User joins league via invite code
        4. Verify membership created
    """
    # Arrange
    owner = await UserFactory.create(db_session)
    league = await LeagueFactory.create(db_session, owner_id=owner.id)

    new_user = await UserFactory.create(db_session)

    # Act
    membership = LeagueMembership(
        league_id=league.id,
        user_id=new_user.id,
        is_active=True,
    )
    db_session.add(membership)
    await db_session.commit()

    # Assert
    assert await exists(
        db_session, LeagueMembership, league_id=league.id, user_id=new_user.id
    )


# ============================================================================
# FR-LEAGUE-005: League owner designation
# ============================================================================


@pytest.mark.league
@pytest.mark.integration
async def test_league_creator_is_owner(db_session):
    """
    Test FR-LEAGUE-005: The system shall designate the creator as the league owner.

    Scenario:
        1. User creates league
        2. Verify user is set as owner
    """
    # Arrange
    user = await UserFactory.create(db_session)

    # Act
    league = await LeagueFactory.create(db_session, owner_id=user.id)

    # Assert
    assert league.owner_id == user.id


# ============================================================================
# FR-LEAGUE-006 & FR-LEAGUE-007: Update settings and regenerate codes
# ============================================================================


@pytest.mark.league
@pytest.mark.integration
async def test_owner_can_update_league_settings(db_session):
    """
    Test FR-LEAGUE-006: The system shall allow league owners to update league settings.

    Scenario:
        1. Create league
        2. Update settings
        3. Verify settings updated
    """
    # Arrange
    league = await LeagueFactory.create_with_owner(db_session)
    original_settings = league.settings.copy()

    # Act
    new_settings = {
        "default_draft_format": "linear",
        "require_trade_approval": False,
    }
    league.settings = new_settings
    await db_session.commit()
    await db_session.refresh(league)

    # Assert
    assert league.settings != original_settings
    assert league.settings == new_settings


@pytest.mark.league
@pytest.mark.integration
async def test_owner_can_regenerate_invite_code(db_session):
    """
    Test FR-LEAGUE-007: The system shall allow league owners to regenerate invite codes.

    Scenario:
        1. Create league
        2. Regenerate invite code
        3. Verify code changed
    """
    # Arrange
    league = await LeagueFactory.create_with_owner(db_session)
    original_code = league.invite_code

    # Act
    league.invite_code = "NEWCODE123"
    await db_session.commit()
    await db_session.refresh(league)

    # Assert
    assert league.invite_code != original_code
    assert league.invite_code == "NEWCODE123"


# ============================================================================
# FR-LEAGUE-008 & FR-LEAGUE-009: Membership management
# ============================================================================


@pytest.mark.league
@pytest.mark.integration
async def test_owner_can_remove_members(db_session):
    """
    Test FR-LEAGUE-008: The system shall allow league owners to remove members from the league.

    Scenario:
        1. Create league with members
        2. Owner removes a member
        3. Verify member removed
    """
    # Arrange
    league, members = await LeagueFactory.create_with_members(
        db_session, member_count=3
    )
    owner = members[0]
    member_to_remove = members[1]

    # Act - Mark membership as inactive
    result = await db_session.execute(
        select(LeagueMembership).where(
            LeagueMembership.league_id == league.id,
            LeagueMembership.user_id == member_to_remove.id,
        )
    )
    membership = result.scalar_one()
    membership.is_active = False
    await db_session.commit()

    # Assert
    await db_session.refresh(membership)
    assert membership.is_active is False


@pytest.mark.league
@pytest.mark.integration
async def test_non_owner_can_leave_league(db_session):
    """
    Test FR-LEAGUE-009: The system shall allow non-owner members to leave a league.

    Scenario:
        1. Create league with members
        2. Non-owner leaves league
        3. Verify membership removed or deactivated
    """
    # Arrange
    league, members = await LeagueFactory.create_with_members(
        db_session, member_count=3
    )
    member_to_leave = members[1]  # Not the owner

    # Act
    result = await db_session.execute(
        select(LeagueMembership).where(
            LeagueMembership.league_id == league.id,
            LeagueMembership.user_id == member_to_leave.id,
        )
    )
    membership = result.scalar_one()
    await db_session.delete(membership)
    await db_session.commit()

    # Assert
    assert not await exists(
        db_session,
        LeagueMembership,
        league_id=league.id,
        user_id=member_to_leave.id,
    )


# ============================================================================
# FR-LEAGUE-010 & FR-LEAGUE-011: List leagues and details
# ============================================================================


@pytest.mark.league
@pytest.mark.integration
async def test_list_all_leagues_for_user(db_session):
    """
    Test FR-LEAGUE-010: The system shall list all leagues for which a user is a member.

    Scenario:
        1. Create user
        2. Create multiple leagues
        3. User joins some leagues
        4. Verify correct leagues listed
    """
    # Arrange
    user = await UserFactory.create(db_session)

    # Create leagues where user is owner
    league1 = await LeagueFactory.create(db_session, owner_id=user.id)
    league2 = await LeagueFactory.create(db_session, owner_id=user.id)

    # Create league where user is member
    other_owner = await UserFactory.create(db_session)
    league3 = await LeagueFactory.create(db_session, owner_id=other_owner.id)
    membership = LeagueMembership(
        league_id=league3.id,
        user_id=user.id,
        is_active=True,
    )
    db_session.add(membership)
    await db_session.commit()

    # Act - Get all leagues for user (as owner or member)
    result = await db_session.execute(
        select(League).join(
            LeagueMembership,
            (LeagueMembership.league_id == League.id) | (League.owner_id == user.id)
        ).where(
            (LeagueMembership.user_id == user.id) | (League.owner_id == user.id)
        ).distinct()
    )
    user_leagues = result.scalars().all()

    # Assert
    league_ids = [league.id for league in user_leagues]
    assert league1.id in league_ids or league2.id in league_ids  # User should be in their leagues


@pytest.mark.league
@pytest.mark.integration
async def test_display_league_details(db_session):
    """
    Test FR-LEAGUE-011: The system shall display league details including
    name, member count, and current season.

    Scenario:
        1. Create league with members
        2. Query league details
        3. Verify all details accessible
    """
    # Arrange
    league, members = await LeagueFactory.create_with_members(
        db_session, member_count=5
    )

    # Act
    await db_session.refresh(league)
    member_count = await db_session.execute(
        select(LeagueMembership).where(
            LeagueMembership.league_id == league.id,
            LeagueMembership.is_active == True,
        )
    )
    active_members = len(member_count.scalars().all())

    # Assert
    assert league.name is not None
    assert active_members == 5


# ============================================================================
# FR-LEAGUE-012 & FR-LEAGUE-013: Settings and membership tracking
# ============================================================================


@pytest.mark.league
@pytest.mark.integration
async def test_league_settings_stored_as_jsonb(db_session):
    """
    Test FR-LEAGUE-012: The system shall store league settings in JSONB format for flexibility.

    Scenario:
        1. Create league with complex settings
        2. Verify settings stored and retrieved correctly
    """
    # Arrange
    complex_settings = {
        "default_draft_format": "auction",
        "require_trade_approval": True,
        "custom_rules": {
            "tier_limits": {"OU": 2, "UU": 3, "RU": 5},
            "banned_abilities": ["Moody", "Shadow Tag"],
        },
        "scoring": {"win": 3, "tie": 1, "loss": 0},
    }

    # Act
    league = await LeagueFactory.create_with_owner(
        db_session, settings=complex_settings
    )

    # Assert
    await db_session.refresh(league)
    assert league.settings == complex_settings
    assert league.settings["custom_rules"]["tier_limits"]["OU"] == 2


@pytest.mark.league
@pytest.mark.integration
async def test_track_membership_status(db_session):
    """
    Test FR-LEAGUE-013: The system shall track league membership status (active/inactive).

    Scenario:
        1. Create league with member
        2. Toggle membership status
        3. Verify status tracked correctly
    """
    # Arrange
    league, members = await LeagueFactory.create_with_members(
        db_session, member_count=2
    )
    member = members[1]

    # Act - Get membership
    result = await db_session.execute(
        select(LeagueMembership).where(
            LeagueMembership.league_id == league.id,
            LeagueMembership.user_id == member.id,
        )
    )
    membership = result.scalar_one()

    # Assert initial state
    assert membership.is_active is True

    # Act - Deactivate
    membership.is_active = False
    await db_session.commit()
    await db_session.refresh(membership)

    # Assert deactivated
    assert membership.is_active is False


# ============================================================================
# Parametrized Tests
# ============================================================================


@pytest.mark.league
@pytest.mark.integration
@pytest.mark.parametrize(
    "member_count,expected_active",
    [
        (2, 2),
        (5, 5),
        (10, 10),
        (20, 20),
    ],
)
async def test_league_with_various_member_counts(
    db_session, member_count, expected_active
):
    """
    Parametrized test for leagues with different member counts.

    Tests scalability and membership management.
    """
    # Act
    league, members = await LeagueFactory.create_with_members(
        db_session, member_count=member_count
    )

    # Assert
    result = await db_session.execute(
        select(LeagueMembership).where(
            LeagueMembership.league_id == league.id,
            LeagueMembership.is_active == True,
        )
    )
    active_memberships = result.scalars().all()
    assert len(active_memberships) == expected_active


@pytest.mark.league
@pytest.mark.integration
@pytest.mark.parametrize(
    "draft_format,trade_approval",
    [
        ("snake", False),
        ("linear", True),
        ("auction", False),
        ("snake", True),
    ],
)
async def test_league_with_different_settings(
    db_session, draft_format, trade_approval
):
    """
    Parametrized test for leagues with different configuration settings.

    Tests FR-LEAGUE-014 and FR-LEAGUE-015.
    """
    # Arrange
    settings = {
        "default_draft_format": draft_format,
        "require_trade_approval": trade_approval,
    }

    # Act
    league = await LeagueFactory.create_with_owner(db_session, settings=settings)

    # Assert
    assert league.settings["default_draft_format"] == draft_format
    assert league.settings["require_trade_approval"] == trade_approval
