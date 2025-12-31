"""
Simple example test to verify the test suite setup works correctly.

This test can be run to verify:
1. Testcontainers is working
2. Database fixtures are working
3. Factories are working
"""

import pytest
from tests.utils.factories import UserFactory, LeagueFactory
from tests.utils.helpers import count_records

from app.models import User, League


@pytest.mark.integration
async def test_basic_setup_verification(db_session):
    """
    Verify basic test setup is working.

    This test checks that:
    - Database connection works
    - Session fixtures work
    - Basic CRUD operations work
    """
    # Assert database is empty initially
    user_count = await count_records(db_session, User)
    assert user_count == 0

    # Create a user
    user = await UserFactory.create(
        db_session,
        email="setup@test.com",
        display_name="Setup Test User"
    )

    # Verify user was created
    assert user.id is not None
    assert user.email == "setup@test.com"

    # Verify count increased
    user_count = await count_records(db_session, User)
    assert user_count == 1


@pytest.mark.integration
async def test_factory_pattern_works(db_session):
    """
    Verify factory pattern is working correctly.

    This test checks that:
    - Factories can create instances
    - Relationships work
    - Batch creation works
    """
    # Create league with owner
    league = await LeagueFactory.create_with_owner(db_session)

    # Verify league created
    assert league.id is not None
    assert league.owner_id is not None

    # Verify owner exists
    user_count = await count_records(db_session, User)
    assert user_count == 1

    # Create batch of users
    users = await UserFactory.create_batch(db_session, count=3)
    assert len(users) == 3

    # Verify total users
    user_count = await count_records(db_session, User)
    assert user_count == 4  # 1 owner + 3 batch


@pytest.mark.integration
async def test_parametrization_example(db_session):
    """
    Simple parametrization example.

    This test demonstrates how parametrization works in the test suite.
    """
    # This is a simple test, but you can add @pytest.mark.parametrize
    # decorator for multiple test cases
    user = await UserFactory.create(db_session)
    assert user is not None
