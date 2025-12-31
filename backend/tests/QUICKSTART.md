# Quick Start Guide - PokeDraft Test Suite

## 🚀 Quick Start

### 1. Ensure Docker is Running

```bash
docker ps
```

If Docker is not running, start Docker Desktop.

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run Example Tests

```bash
# Run the simple example test to verify setup
pytest tests/test_example.py -v

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## 📋 Test Categories

Run tests by category using markers:

```bash
# Authentication tests
pytest -m auth -v

# League management tests
pytest -m league -v

# Draft management tests
pytest -m draft -v

# Pokemon data tests
pytest -m pokemon -v

# All integration tests
pytest -m integration -v
```

## 🎯 Example: Running Your First Test

```bash
# Run a single test file
pytest tests/integration/test_auth.py -v

# Run a specific test
pytest tests/integration/test_auth.py::test_user_can_update_display_name -v
```

## 📝 Writing Your First Test

1. Choose the appropriate test file in `tests/integration/`
2. Use the test template:

```python
@pytest.mark.{category}
@pytest.mark.integration
async def test_my_feature(db_session):
    """
    Test FR-{CATEGORY}-{NUMBER}: {Description}

    Scenario:
        1. Setup test data
        2. Perform action
        3. Verify result
    """
    # Arrange - Setup
    user = await UserFactory.create(db_session)

    # Act - Perform action
    user.display_name = "New Name"
    await db_session.commit()

    # Assert - Verify
    assert user.display_name == "New Name"
```

3. Run your test:

```bash
pytest tests/integration/test_yourfile.py::test_my_feature -v
```

## 🔧 Common Commands

```bash
# Run all tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=app --cov-report=term-missing

# Run tests in parallel (faster)
pip install pytest-xdist
pytest -n auto

# Run only fast tests (exclude slow)
pytest -m "not slow"

# Show available markers
pytest --markers
```

## 📚 Available Factories

Create test data easily:

```python
from tests.utils.factories import (
    UserFactory,
    LeagueFactory,
    SeasonFactory,
    DraftFactory,
    TeamFactory,
    PokemonFactory,
)

# Simple creation
user = await UserFactory.create(db_session)

# Custom values
user = await UserFactory.create(
    db_session,
    email="custom@test.com",
    display_name="Custom User"
)

# Batch creation
users = await UserFactory.create_batch(db_session, count=10)

# With relationships
league, members = await LeagueFactory.create_with_members(
    db_session,
    member_count=5
)
```

## 🐛 Troubleshooting

### Docker not running
**Error**: `Docker is not running or not installed`
**Fix**: Start Docker Desktop

### Tests fail with connection error
**Fix**:
1. Check Docker has enough resources (Memory: 4GB+)
2. Restart Docker
3. Pull postgres image manually: `docker pull postgres:15-alpine`

### Import errors
**Fix**:
```bash
# Make sure you're in the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
```

## 📖 Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore existing tests in `tests/integration/`
3. Review factories in `tests/utils/factories.py`
4. Check helpers in `tests/utils/helpers.py`

## 🎓 Learn More

- See [README.md](README.md) for comprehensive documentation
- Check [REQUIREMENTS.md](../../REQUIREMENTS.md) for requirement specifications
- Review existing tests for patterns and examples

---

**Happy Testing!** 🧪
