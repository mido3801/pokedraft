"""
Pytest configuration and fixtures for PokeDraft tests.

This module provides reusable fixtures using testcontainers for PostgreSQL,
with emphasis on reusability, parametrization, and ease of creating future tests.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.core.database import Base
from app.models import *  # noqa: F401, F403 - Import all models to register them


# ============================================================================
# Session and Module Scoped Fixtures (Database Container)
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the entire test session.
    This ensures async fixtures work properly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """
    Provides a PostgreSQL container for the entire test session.
    Uses testcontainers to spin up a real PostgreSQL instance.

    Scope: session - Container is created once and reused across all tests.
    """
    with PostgresContainer("postgres:15-alpine") as postgres:
        # Wait for postgres to be ready
        postgres.get_connection_url()
        yield postgres


@pytest.fixture(scope="session")
def postgres_url(postgres_container: PostgresContainer) -> str:
    """
    Get the async PostgreSQL connection URL from the container.

    Scope: session - URL is constant for the entire session.
    """
    url = postgres_container.get_connection_url()
    # Convert to async driver
    return url.replace("psycopg2", "asyncpg")


# ============================================================================
# Function Scoped Fixtures (Clean Database per Test)
# ============================================================================


@pytest_asyncio.fixture
async def test_engine(postgres_url: str):
    """
    Create a test database engine for each test.

    Scope: function - New engine per test ensures isolation.
    """
    engine = create_async_engine(
        postgres_url,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup: Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session_maker(test_engine):
    """
    Create an async session maker for tests.

    Scope: function - New session maker per test.
    """
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def db_session(async_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a clean database session for each test.
    Automatically rolls back transactions after each test.

    Scope: function - Fresh session per test ensures test isolation.

    Usage:
        async def test_something(db_session):
            user = User(email="test@example.com")
            db_session.add(user)
            await db_session.commit()
    """
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def db_session_commit(async_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session that commits changes.
    Use this when you need changes to persist within a test
    (e.g., testing cascade deletes, triggers, etc.)

    Scope: function - Fresh session per test.

    Usage:
        async def test_cascade_delete(db_session_commit):
            # Changes are committed and visible to other queries
            pass
    """
    async with async_session_maker() as session:
        yield session
        await session.commit()


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def override_settings():
    """
    Fixture to override application settings for tests.

    Usage:
        def test_with_custom_settings(override_settings):
            override_settings(DEV_MODE=True, SECRET_KEY="test")
    """
    from app.core.config import settings
    original_values = {}

    def _override(**kwargs):
        for key, value in kwargs.items():
            original_values[key] = getattr(settings, key, None)
            setattr(settings, key, value)

    yield _override

    # Restore original values
    for key, value in original_values.items():
        setattr(settings, key, value)


@pytest_asyncio.fixture
async def clean_db(test_engine):
    """
    Fixture to ensure database is completely clean.
    Useful for integration tests that need a fresh state.

    Usage:
        async def test_clean_state(clean_db, db_session):
            # Database is guaranteed to be empty
            pass
    """
    async with test_engine.begin() as conn:
        # Truncate all tables
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
        await conn.commit()


# ============================================================================
# Parametrization Helpers
# ============================================================================


def pytest_configure(config):
    """
    Register custom markers for better test organization.
    """
    config.addinivalue_line(
        "markers", "auth: Tests for authentication requirements (FR-AUTH-*)"
    )
    config.addinivalue_line(
        "markers", "league: Tests for league management requirements (FR-LEAGUE-*)"
    )
    config.addinivalue_line(
        "markers", "season: Tests for season management requirements (FR-SEASON-*)"
    )
    config.addinivalue_line(
        "markers", "draft: Tests for draft management requirements (FR-DRAFT-*)"
    )
    config.addinivalue_line(
        "markers", "team: Tests for team management requirements (FR-TEAM-*)"
    )
    config.addinivalue_line(
        "markers", "trade: Tests for trading requirements (FR-TRADE-*)"
    )
    config.addinivalue_line(
        "markers", "match: Tests for match management requirements (FR-MATCH-*)"
    )
    config.addinivalue_line(
        "markers", "pokemon: Tests for Pokemon data requirements (FR-POKE-*)"
    )
    config.addinivalue_line(
        "markers", "websocket: Tests for WebSocket requirements (FR-WS-*)"
    )
    config.addinivalue_line(
        "markers", "performance: Tests for performance requirements (NFR-PERF-*)"
    )
    config.addinivalue_line(
        "markers", "security: Tests for security requirements (NFR-SEC-*)"
    )


# ============================================================================
# Docker Environment Detection
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def check_docker():
    """
    Automatically check if Docker is available before running tests.
    Provides a clear error message if Docker is not running.
    """
    import subprocess

    try:
        subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            check=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pytest.exit(
            "Docker is not running or not installed. "
            "Testcontainers requires Docker to run tests. "
            "Please start Docker and try again."
        )
