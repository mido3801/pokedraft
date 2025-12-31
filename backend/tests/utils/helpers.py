"""
Helper utilities for tests.

This module provides common helper functions for assertions,
data validation, and test utilities.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# Database Helpers
# ============================================================================


async def count_records(db_session: AsyncSession, model_class) -> int:
    """
    Count total records for a model.

    Args:
        db_session: Database session
        model_class: SQLAlchemy model class

    Returns:
        Number of records
    """
    result = await db_session.execute(select(model_class))
    return len(result.scalars().all())


async def get_by_id(db_session: AsyncSession, model_class, id: int):
    """
    Get a record by ID.

    Args:
        db_session: Database session
        model_class: SQLAlchemy model class
        id: Record ID

    Returns:
        Model instance or None
    """
    result = await db_session.execute(
        select(model_class).where(model_class.id == id)
    )
    return result.scalar_one_or_none()


async def exists(db_session: AsyncSession, model_class, **filters) -> bool:
    """
    Check if a record exists with given filters.

    Args:
        db_session: Database session
        model_class: SQLAlchemy model class
        **filters: Column filters

    Returns:
        True if record exists, False otherwise
    """
    query = select(model_class)
    for key, value in filters.items():
        query = query.where(getattr(model_class, key) == value)

    result = await db_session.execute(query)
    return result.scalar_one_or_none() is not None


async def get_all(db_session: AsyncSession, model_class) -> List:
    """
    Get all records for a model.

    Args:
        db_session: Database session
        model_class: SQLAlchemy model class

    Returns:
        List of model instances
    """
    result = await db_session.execute(select(model_class))
    return result.scalars().all()


# ============================================================================
# Assertion Helpers
# ============================================================================


def assert_model_fields(instance: Any, expected: Dict[str, Any]):
    """
    Assert that a model instance has expected field values.

    Args:
        instance: Model instance
        expected: Dictionary of field_name: expected_value

    Raises:
        AssertionError: If any field doesn't match
    """
    for field, value in expected.items():
        actual = getattr(instance, field)
        assert actual == value, f"Field {field}: expected {value}, got {actual}"


def assert_dict_subset(subset: Dict, superset: Dict):
    """
    Assert that subset is contained in superset.

    Args:
        subset: Dictionary that should be contained
        superset: Dictionary that should contain subset

    Raises:
        AssertionError: If subset is not contained in superset
    """
    for key, value in subset.items():
        assert key in superset, f"Key {key} not found in superset"
        assert superset[key] == value, f"Key {key}: expected {value}, got {superset[key]}"


# ============================================================================
# Data Validation Helpers
# ============================================================================


def validate_timestamp_recent(timestamp, max_seconds: int = 60):
    """
    Validate that a timestamp is recent (within max_seconds).

    Args:
        timestamp: datetime object to validate
        max_seconds: Maximum age in seconds

    Raises:
        AssertionError: If timestamp is too old or None
    """
    from datetime import datetime, timezone

    assert timestamp is not None, "Timestamp is None"
    now = datetime.now(timezone.utc)
    age = (now - timestamp.replace(tzinfo=timezone.utc)).total_seconds()
    assert age <= max_seconds, f"Timestamp is {age}s old, expected <= {max_seconds}s"


def validate_uuid_format(value: str):
    """
    Validate that a string is a valid UUID.

    Args:
        value: String to validate

    Raises:
        AssertionError: If string is not a valid UUID
    """
    import uuid

    try:
        uuid.UUID(value)
    except ValueError:
        raise AssertionError(f"'{value}' is not a valid UUID")


def validate_email_format(email: str):
    """
    Validate that a string is a valid email format.

    Args:
        email: String to validate

    Raises:
        AssertionError: If string is not a valid email
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    assert re.match(pattern, email), f"'{email}' is not a valid email format"


# ============================================================================
# Parametrization Helpers
# ============================================================================


def generate_test_cases(base_params: Dict, variations: List[Dict]) -> List[Dict]:
    """
    Generate test case variations by combining base parameters with variations.

    Args:
        base_params: Base parameters common to all cases
        variations: List of parameter variations

    Returns:
        List of complete parameter dictionaries

    Example:
        base = {"format": "snake", "roster_size": 6}
        variations = [
            {"timer_seconds": 30},
            {"timer_seconds": 60},
            {"timer_seconds": 90},
        ]
        cases = generate_test_cases(base, variations)
        # Returns: [
        #     {"format": "snake", "roster_size": 6, "timer_seconds": 30},
        #     {"format": "snake", "roster_size": 6, "timer_seconds": 60},
        #     {"format": "snake", "roster_size": 6, "timer_seconds": 90},
        # ]
    """
    return [{**base_params, **variation} for variation in variations]


# ============================================================================
# Mock Data Helpers
# ============================================================================


def generate_pokemon_pool_data(
    pokemon_ids: Optional[List[int]] = None,
    filters: Optional[Dict] = None,
    point_values: Optional[Dict[int, int]] = None,
) -> Dict:
    """
    Generate a mock Pokemon pool configuration.

    Args:
        pokemon_ids: List of Pokemon IDs in the pool
        filters: Filter configuration
        point_values: Custom point values per Pokemon ID

    Returns:
        Pokemon pool data dictionary
    """
    return {
        "pool": pokemon_ids or [],
        "filters": filters or {
            "generations": [1, 2, 3],
            "include_legendary": False,
            "include_mythical": False,
        },
        "point_values": point_values or {},
    }


def generate_league_settings(
    draft_format: str = "snake",
    require_trade_approval: bool = False,
    **kwargs,
) -> Dict:
    """
    Generate league settings configuration.

    Args:
        draft_format: Default draft format
        require_trade_approval: Whether trades need admin approval
        **kwargs: Additional settings

    Returns:
        League settings dictionary
    """
    settings = {
        "default_draft_format": draft_format,
        "require_trade_approval": require_trade_approval,
    }
    settings.update(kwargs)
    return settings


def generate_season_settings(
    max_teams: int = 8,
    schedule_format: str = "round_robin",
    **kwargs,
) -> Dict:
    """
    Generate season settings configuration.

    Args:
        max_teams: Maximum number of teams
        schedule_format: Schedule format type
        **kwargs: Additional settings

    Returns:
        Season settings dictionary
    """
    settings = {
        "max_teams": max_teams,
        "schedule_format": schedule_format,
    }
    settings.update(kwargs)
    return settings
