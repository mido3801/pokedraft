"""
Database utility functions for common query patterns.

Provides reusable helpers to reduce boilerplate in API endpoints.
"""

from typing import Any, Callable, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError

T = TypeVar("T")


async def fetch_or_404(
    db: AsyncSession,
    model: Type[T],
    id_value: UUID,
    error_fn: Callable[[Any], NotFoundError],
) -> T:
    """
    Fetch a single record by ID or raise a 404 error.

    Args:
        db: Database session
        model: SQLAlchemy model class
        id_value: The ID to look up
        error_fn: Function that creates the appropriate NotFoundError

    Returns:
        The found model instance

    Raises:
        NotFoundError: If no record is found with the given ID

    Example:
        draft = await fetch_or_404(db, DraftModel, draft_id, draft_not_found)
    """
    result = await db.execute(select(model).where(model.id == id_value))
    obj = result.scalar_one_or_none()
    if not obj:
        raise error_fn(id_value)
    return obj


async def fetch_optional(
    db: AsyncSession,
    model: Type[T],
    id_value: UUID,
) -> T | None:
    """
    Fetch a single record by ID, returning None if not found.

    Args:
        db: Database session
        model: SQLAlchemy model class
        id_value: The ID to look up

    Returns:
        The found model instance or None
    """
    result = await db.execute(select(model).where(model.id == id_value))
    return result.scalar_one_or_none()
