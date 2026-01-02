"""Database session management for the Discord bot.

The bot uses direct database access with the same SQLAlchemy models
as the main backend, sharing the same async engine and session maker.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for bot operations.

    Usage:
        async with get_db_session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async generator for database sessions (dependency injection style).

    Usage with discord.py cogs:
        async with get_db() as db:
            # use db
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
