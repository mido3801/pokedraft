# PokeDraft Test Suite

Comprehensive test suite for the PokeDraft system using pytest, testcontainers, and PostgreSQL.

## Overview

This test suite is designed with emphasis on:
- **Reusability**: Fixtures and factories that can be reused across tests
- **Parametrization**: Easy creation of test variations with pytest.mark.parametrize
- **Isolation**: Each test runs with a clean database state
- **Real Database**: Uses testcontainers with PostgreSQL (not SQLite)
- **Extensibility**: Easy to add new tests following established patterns

## Prerequisites

- Docker installed and running (required for testcontainers)
- Python 3.9+
- All dependencies installed from requirements.txt

## Installation

```bash
# Install test dependencies
pip install -r requirements.txt

# Verify Docker is running
docker ps
```

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test categories
```bash
# Run only authentication tests
pytest -m auth

# Run only integration tests
pytest -m integration

# Run only league tests
pytest -m league

# Run specific test file
pytest tests/integration/test_auth.py

# Run specific test function
pytest tests/integration/test_auth.py::test_user_can_update_display_name
```

### Run tests with verbose output
```bash
pytest -v
```

### Run tests excluding slow tests
```bash
pytest -m "not slow"
```

## Test Structure

```
tests/
├── conftest.py              # Global fixtures and configuration
├── __init__.py
├── fixtures/                # Reusable test fixtures
│   ├── __init__.py
│   └── auth_fixtures.py     # Auth-specific fixtures
├── utils/                   # Test utilities
│   ├── __init__.py
│   ├── factories.py         # Factory functions for creating test data
│   └── helpers.py           # Helper functions for assertions and queries
├── integration/             # Integration tests
│   ├── __init__.py
│   ├── test_auth.py         # FR-AUTH-* tests
│   ├── test_league.py       # FR-LEAGUE-* tests
│   ├── test_draft.py        # FR-DRAFT-* tests
│   └── test_pokemon.py      # FR-POKE-* tests
└── unit/                    # Unit tests (to be added)
    └── __init__.py
```

## Key Components

### 1. Testcontainers Setup (conftest.py)

The test suite uses testcontainers to spin up a real PostgreSQL database for each test session:

```python
@pytest.fixture(scope="session")
def postgres_container() -> PostgresContainer:
    """Provides a PostgreSQL container for the entire test session."""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres
```

**Benefits:**
- Tests against real PostgreSQL (not SQLite)
- Isolated database per test session
- Automatically cleaned up after tests
- Tests the actual database features (JSONB, indexes, etc.)

### 2. Database Fixtures

#### Session-scoped fixtures (created once):
- `postgres_container`: PostgreSQL container
- `postgres_url`: Connection URL

#### Function-scoped fixtures (created per test):
- `test_engine`: Fresh database engine
- `async_session_maker`: Session maker
- `db_session`: Clean database session with auto-rollback
- `db_session_commit`: Database session that commits changes

### 3. Factory Pattern

Factories provide easy test data creation with sensible defaults:

```python
from tests.utils.factories import UserFactory, LeagueFactory

async def test_example(db_session):
    # Create with defaults
    user = await UserFactory.create(db_session)

    # Create with custom values
    user = await UserFactory.create(
        db_session,
        email="custom@test.com",
        display_name="Custom User"
    )

    # Create multiple instances
    users = await UserFactory.create_batch(db_session, count=5)

    # Create with relationships
    league = await LeagueFactory.create_with_owner(db_session)
    league, members = await LeagueFactory.create_with_members(
        db_session,
        member_count=10
    )
```

Available factories:
- `UserFactory`
- `LeagueFactory`
- `SeasonFactory`
- `DraftFactory`
- `TeamFactory`
- `PokemonFactory`
- `TradeFactory`
- `MatchFactory`
- `PoolPresetFactory`

### 4. Helper Utilities

Located in `tests/utils/helpers.py`:

```python
from tests.utils.helpers import (
    count_records,
    exists,
    assert_model_fields,
    validate_timestamp_recent,
)

async def test_example(db_session):
    # Count records
    count = await count_records(db_session, User)

    # Check existence
    user_exists = await exists(db_session, User, email="test@example.com")

    # Assert model fields
    assert_model_fields(user, {
        "email": "test@example.com",
        "display_name": "Test User"
    })

    # Validate timestamp
    validate_timestamp_recent(user.created_at, max_seconds=60)
```

## Test Markers

Tests are organized with markers for easy filtering:

- `@pytest.mark.auth` - Authentication tests (FR-AUTH-*)
- `@pytest.mark.league` - League management tests (FR-LEAGUE-*)
- `@pytest.mark.season` - Season management tests (FR-SEASON-*)
- `@pytest.mark.draft` - Draft management tests (FR-DRAFT-*)
- `@pytest.mark.team` - Team management tests (FR-TEAM-*)
- `@pytest.mark.trade` - Trading tests (FR-TRADE-*)
- `@pytest.mark.match` - Match management tests (FR-MATCH-*)
- `@pytest.mark.pokemon` - Pokemon data tests (FR-POKE-*)
- `@pytest.mark.websocket` - WebSocket tests (FR-WS-*)
- `@pytest.mark.performance` - Performance tests (NFR-PERF-*)
- `@pytest.mark.security` - Security tests (NFR-SEC-*)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.slow` - Slow-running tests

## Writing New Tests

### Example 1: Simple Test

```python
@pytest.mark.auth
@pytest.mark.integration
async def test_user_creation(db_session):
    """
    Test FR-AUTH-008: Auto-create user from token metadata.

    Scenario:
        1. Create user with metadata
        2. Verify user persisted
    """
    # Arrange
    user = await UserFactory.create(
        db_session,
        email="test@example.com"
    )

    # Assert
    assert user.id is not None
    assert user.email == "test@example.com"
```

### Example 2: Parametrized Test

```python
@pytest.mark.draft
@pytest.mark.integration
@pytest.mark.parametrize(
    "format,roster_size,timer",
    [
        ("snake", 6, 90),
        ("linear", 8, 120),
        ("auction", 10, 60),
    ],
)
async def test_draft_configurations(db_session, format, roster_size, timer):
    """Test various draft configurations."""
    # Act
    draft = await DraftFactory.create(
        db_session,
        format=format,
        roster_size=roster_size,
        timer_seconds=timer,
    )

    # Assert
    assert draft.format == format
    assert draft.roster_size == roster_size
    assert draft.timer_seconds == timer
```

### Example 3: Test with Relationships

```python
@pytest.mark.league
@pytest.mark.integration
async def test_league_with_members(db_session):
    """Test FR-LEAGUE-003: Join league with invite code."""
    # Arrange
    league, members = await LeagueFactory.create_with_members(
        db_session,
        member_count=5
    )

    # Assert
    assert len(members) == 5
    assert league.owner_id == members[0].id
```

## Test Organization Best Practices

1. **Group Related Tests**: Use test classes or modules for related functionality
2. **Clear Test Names**: Use descriptive names like `test_user_can_update_display_name`
3. **Document Requirements**: Link tests to requirements in docstrings
4. **AAA Pattern**: Structure tests with Arrange, Act, Assert sections
5. **Use Markers**: Tag tests with appropriate markers for filtering
6. **Parametrize When Possible**: Use parametrization for testing multiple scenarios

## Continuous Integration

For CI/CD pipelines, ensure Docker is available:

```yaml
# Example GitHub Actions
- name: Start containers
  run: docker compose up -d postgres

- name: Run tests
  run: pytest --cov --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Coverage

To generate and view coverage reports:

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

Target coverage: 80%+ for critical paths

## Troubleshooting

### Docker not running
```
Error: Docker is not running or not installed
```
**Solution**: Start Docker Desktop or Docker daemon

### Port already in use
```
Error: Port 5432 is already in use
```
**Solution**: Stop other PostgreSQL instances or use a different port

### Slow test execution
```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

### Database connection issues
- Verify Docker has enough resources allocated
- Check if testcontainers can pull postgres:15-alpine image
- Ensure no firewall blocking local Docker connections

## Adding Tests for New Requirements

When adding tests for new requirements:

1. **Identify the requirement category** (AUTH, LEAGUE, DRAFT, etc.)
2. **Create or extend test file** in `tests/integration/`
3. **Add marker** for the requirement category
4. **Use factories** for test data creation
5. **Follow AAA pattern** (Arrange, Act, Assert)
6. **Document the requirement** in the test docstring
7. **Add parametrization** for multiple scenarios if applicable

Example template:

```python
@pytest.mark.{category}
@pytest.mark.integration
async def test_{requirement_description}(db_session):
    """
    Test FR-{CATEGORY}-{NUMBER}: {Requirement text}

    Scenario:
        1. {Step 1}
        2. {Step 2}
        3. {Step 3}
    """
    # Arrange
    {setup_code}

    # Act
    {action_code}

    # Assert
    {assertion_code}
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [testcontainers-python documentation](https://testcontainers-python.readthedocs.io/)
- [SQLAlchemy async documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Faker documentation](https://faker.readthedocs.io/)

## Next Steps

To extend the test suite:

1. Add unit tests for services and utilities
2. Add WebSocket tests for real-time features
3. Add performance tests for scalability requirements
4. Add security tests for authentication and authorization
5. Add end-to-end API tests using TestClient
6. Add load tests for concurrent operations

## Support

For questions or issues with the test suite:
1. Check this README
2. Review existing tests for examples
3. Check the conftest.py for available fixtures
4. Review the factories.py for data creation patterns
