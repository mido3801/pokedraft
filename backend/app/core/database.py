from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


def get_async_database_url() -> str:
    """Convert standard PostgreSQL URL to async version."""
    url = settings.DATABASE_URL
    if not url:
        return "postgresql+asyncpg://postgres:postgres@localhost:5432/pokedraft"
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_sync_database_url() -> str:
    """Get standard PostgreSQL URL for sync operations (migrations)."""
    url = settings.DATABASE_URL
    if not url:
        return "postgresql://postgres:postgres@localhost:5432/pokedraft"
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
