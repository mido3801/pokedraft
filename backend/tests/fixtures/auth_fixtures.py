"""
Reusable fixtures for authentication testing.

These fixtures provide common auth-related test data and utilities
for testing authentication requirements (FR-AUTH-*).
"""

import pytest
import pytest_asyncio
from tests.utils.factories import UserFactory


@pytest_asyncio.fixture
async def test_user(db_session):
    """
    Provides a standard test user.

    Usage:
        async def test_something(test_user):
            assert test_user.email is not None
    """
    return await UserFactory.create(
        db_session,
        email="test@example.com",
        display_name="Test User",
    )


@pytest_asyncio.fixture
async def test_users(db_session):
    """
    Provides multiple test users for batch operations.

    Returns:
        List of 4 test users
    """
    users = []
    for i in range(4):
        user = await UserFactory.create(
            db_session,
            email=f"test{i+1}@example.com",
            display_name=f"Test User {i+1}",
        )
        users.append(user)
    return users


@pytest_asyncio.fixture
async def user_with_discord(db_session):
    """
    Provides a test user with Discord linked.

    Tests FR-AUTH-005: Discord account linking
    """
    return await UserFactory.create(
        db_session,
        email="discord@example.com",
        display_name="Discord User",
        discord_id="123456789",
        discord_username="testuser#1234",
    )


@pytest.fixture
def mock_jwt_token():
    """
    Provides a mock JWT token structure for testing.

    Tests FR-AUTH-006 and FR-AUTH-007: JWT validation
    """
    return {
        "sub": "user-id-123",
        "email": "test@example.com",
        "aud": "authenticated",
        "exp": 1735689600,  # Future timestamp
        "iat": 1735603200,
        "user_metadata": {
            "display_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
        },
    }


@pytest.fixture
def dev_mode_token():
    """
    Provides a development mode token for testing.

    Tests FR-AUTH-003 and FR-AUTH-007: Dev mode quick login
    """
    import jwt
    from datetime import datetime, timedelta

    payload = {
        "sub": "dev-user-1",
        "email": "dev1@example.com",
        "exp": datetime.utcnow() + timedelta(days=1),
        "dev_mode": True,
    }

    return jwt.encode(payload, "dev-secret", algorithm="HS256")


@pytest.fixture
def anonymous_session_token():
    """
    Provides an anonymous session token.

    Tests FR-AUTH-010 and FR-AUTH-011: Anonymous draft participation
    """
    import secrets

    return secrets.token_urlsafe(32)
