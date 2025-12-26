from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


def get_async_database_url() -> str:
    """Convert standard PostgreSQL URL to async version.

    Handles various URL formats:
    - postgres:// (Supabase/Heroku style)
    - postgresql://
    - postgresql+asyncpg://
    """
    url = settings.DATABASE_URL
    if not url:
        return "postgresql+asyncpg://postgres:postgres@localhost:5432/pokedraft"
    # Handle postgres:// scheme (used by Supabase and Heroku)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_sync_database_url() -> str:
    """Get standard PostgreSQL URL for sync operations (migrations).

    Handles various URL formats:
    - postgres:// (Supabase/Heroku style)
    - postgresql://
    - postgresql+asyncpg://
    """
    url = settings.DATABASE_URL
    if not url:
        return "postgresql://postgres:postgres@localhost:5432/pokedraft"
    # Handle postgres:// scheme (used by Supabase and Heroku)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


engine = create_async_engine(
    get_async_database_url(),
    echo=False,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency for getting database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
