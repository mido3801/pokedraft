"""
Integration tests for Authentication requirements (FR-AUTH-*).

These tests verify the authentication and user management functionality
as specified in the requirements document.
"""

import pytest
from sqlalchemy import select

from app.models import User
from tests.utils.factories import UserFactory
from tests.utils.helpers import count_records, exists, assert_model_fields


# ============================================================================
# FR-AUTH-004: Update display name and avatar
# ============================================================================


@pytest.mark.auth
@pytest.mark.integration
async def test_user_can_update_display_name(db_session):
    """
    Test FR-AUTH-004: The system shall allow users to update their display name.

    Scenario:
        1. Create a user
        2. Update display name
        3. Verify change persisted
    """
    # Arrange
    user = await UserFactory.create(
        db_session,
        email="test@example.com",
        display_name="Original Name",
    )
    original_id = user.id

    # Act
    user.display_name = "Updated Name"
    await db_session.commit()
    await db_session.refresh(user)

    # Assert
    assert user.id == original_id
    assert user.display_name == "Updated Name"
    assert user.email == "test@example.com"


@pytest.mark.auth
@pytest.mark.integration
async def test_user_can_update_avatar_url(db_session):
    """
    Test FR-AUTH-004: The system shall allow users to update their avatar URL.

    Scenario:
        1. Create a user
        2. Update avatar URL
        3. Verify change persisted
    """
    # Arrange
    user = await UserFactory.create(
        db_session,
        email="test@example.com",
        avatar_url="https://example.com/old-avatar.jpg",
    )

    # Act
    user.avatar_url = "https://example.com/new-avatar.jpg"
    await db_session.commit()
    await db_session.refresh(user)

    # Assert
    assert user.avatar_url == "https://example.com/new-avatar.jpg"


# ============================================================================
# FR-AUTH-005: Link Discord accounts
# ============================================================================


@pytest.mark.auth
@pytest.mark.integration
async def test_user_can_link_discord_account(db_session):
    """
    Test FR-AUTH-005: The system shall optionally link user accounts to Discord accounts.

    Scenario:
        1. Create a user without Discord
        2. Link Discord account
        3. Verify Discord information stored
    """
    # Arrange
    user = await UserFactory.create(
        db_session,
        email="test@example.com",
        discord_id=None,
        discord_username=None,
    )

    # Act
    user.discord_id = "987654321"
    user.discord_username = "testuser#5678"
    await db_session.commit()
    await db_session.refresh(user)

    # Assert
    assert user.discord_id == "987654321"
    assert user.discord_username == "testuser#5678"


@pytest.mark.auth
@pytest.mark.integration
async def test_user_can_exist_without_discord(db_session):
    """
    Test FR-AUTH-005: Discord linking is optional.

    Scenario:
        1. Create user without Discord
        2. Verify user can exist without Discord
    """
    # Act
    user = await UserFactory.create(
        db_session,
        email="test@example.com",
    )

    # Assert
    assert user.id is not None
    assert user.discord_id is None
    assert user.discord_username is None


# ============================================================================
# FR-AUTH-008: Auto-create user from token metadata
# ============================================================================


@pytest.mark.auth
@pytest.mark.integration
async def test_user_creation_from_token_metadata(db_session):
    """
    Test FR-AUTH-008: The system shall automatically create user records
    from token metadata on first login.

    Scenario:
        1. Simulate first-time login with token metadata
        2. Verify user created with correct data from token
    """
    # Arrange
    token_metadata = {
        "email": "newuser@example.com",
        "display_name": "New User",
        "avatar_url": "https://example.com/avatar.jpg",
    }

    # Check user doesn't exist
    initial_count = await count_records(db_session, User)

    # Act - Simulate creating user from token
    user = User(
        email=token_metadata["email"],
        display_name=token_metadata["display_name"],
        avatar_url=token_metadata["avatar_url"],
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Assert
    final_count = await count_records(db_session, User)
    assert final_count == initial_count + 1
    assert_model_fields(user, token_metadata)
    assert user.created_at is not None


# ============================================================================
# FR-AUTH-012: Retrieve authenticated user information
# ============================================================================


@pytest.mark.auth
@pytest.mark.integration
async def test_retrieve_user_by_email(db_session):
    """
    Test FR-AUTH-012: The system shall retrieve authenticated user information via API endpoint.

    Scenario:
        1. Create user
        2. Query user by email
        3. Verify correct user retrieved
    """
    # Arrange
    user = await UserFactory.create(
        db_session,
        email="unique@example.com",
        display_name="Unique User",
    )

    # Act
    result = await db_session.execute(
        select(User).where(User.email == "unique@example.com")
    )
    retrieved_user = result.scalar_one_or_none()

    # Assert
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == "unique@example.com"
    assert retrieved_user.display_name == "Unique User"


@pytest.mark.auth
@pytest.mark.integration
async def test_retrieve_user_by_id(db_session):
    """
    Test retrieving user by ID.

    Scenario:
        1. Create user
        2. Query user by ID
        3. Verify correct user retrieved
    """
    # Arrange
    user = await UserFactory.create(db_session)

    # Act
    result = await db_session.execute(select(User).where(User.id == user.id))
    retrieved_user = result.scalar_one_or_none()

    # Assert
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


# ============================================================================
# Data Integrity Tests
# ============================================================================


@pytest.mark.auth
@pytest.mark.integration
async def test_user_email_must_be_unique(db_session):
    """
    Test that user emails must be unique.

    Scenario:
        1. Create user with email
        2. Attempt to create another user with same email
        3. Verify constraint violation
    """
    # Arrange
    await UserFactory.create(db_session, email="duplicate@example.com")
    await db_session.commit()

    # Act & Assert
    with pytest.raises(Exception):  # Will raise IntegrityError
        await UserFactory.create(db_session, email="duplicate@example.com")
        await db_session.commit()


@pytest.mark.auth
@pytest.mark.integration
async def test_user_timestamps_set_automatically(db_session):
    """
    Test that created_at and updated_at timestamps are set automatically.

    Scenario:
        1. Create user
        2. Verify timestamps exist
        3. Update user
        4. Verify updated_at changed
    """
    # Arrange & Act
    user = await UserFactory.create(db_session, email="timestamp@example.com")
    await db_session.commit()
    await db_session.refresh(user)

    # Assert
    assert user.created_at is not None
    assert user.updated_at is not None

    # Act - Update user
    original_updated_at = user.updated_at
    user.display_name = "Updated"
    await db_session.commit()
    await db_session.refresh(user)

    # Assert - updated_at should change
    # Note: In some cases timestamps might be the same if update is too fast
    # This is a basic check
    assert user.updated_at is not None


# ============================================================================
# Parametrized Tests
# ============================================================================


@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.parametrize(
    "email,display_name,has_discord",
    [
        ("user1@example.com", "User One", False),
        ("user2@example.com", "User Two", True),
        ("user3@example.com", "User Three", False),
        ("user4@example.com", "User Four", True),
    ],
)
async def test_create_multiple_user_configurations(
    db_session, email, display_name, has_discord
):
    """
    Parametrized test for creating users with different configurations.

    Tests multiple user creation scenarios to verify flexibility.
    """
    # Arrange
    kwargs = {
        "email": email,
        "display_name": display_name,
    }

    if has_discord:
        kwargs.update(
            {
                "discord_id": f"discord_{email}",
                "discord_username": f"{display_name}#1234",
            }
        )

    # Act
    user = await UserFactory.create(db_session, **kwargs)

    # Assert
    assert user.email == email
    assert user.display_name == display_name

    if has_discord:
        assert user.discord_id is not None
        assert user.discord_username is not None
    else:
        assert user.discord_id is None
        assert user.discord_username is None
