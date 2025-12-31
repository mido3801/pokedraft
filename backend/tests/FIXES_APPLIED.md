# Test Suite Fixes Applied

## Summary of Fixes

The following fixes were applied to align the test factories with the actual model definitions:

### 1. User Model
- **Changed**: `discord_user_id` → `discord_id`
- **Files affected**:
  - `tests/utils/factories.py`
  - `tests/fixtures/auth_fixtures.py`
  - `tests/integration/test_auth.py`

### 2. Draft Model
- **Changed**: `budget_amount` → `budget_per_team`
- **Changed**: `creator_token` → `session_token`
- **Added**: `creator_id`, `started_at`, `completed_at` parameters
- **Files affected**:
  - `tests/utils/factories.py`
  - `tests/integration/test_draft.py`

### 3. Pokemon Model
- **Changed**: `name` → `identifier`
- **Changed**: Pokemon now requires PokemonSpecies relationship
- **Updated**: PokemonFactory.create() now automatically creates species
- **Files affected**:
  - `tests/utils/factories.py`
  - `tests/integration/test_pokemon.py`

### 4. LeagueMembership Model
- **Changed**: `active` → `is_active`
- **Files affected**:
  - `tests/utils/factories.py`
  - `tests/integration/test_league.py`

## Running Tests

### IMPORTANT: Use the virtual environment

The tests must be run using the virtual environment's Python to ensure all dependencies are available:

```bash
# Activate virtual environment
cd backend
source venv/bin/activate

# Run specific test file
python -m pytest tests/test_example.py -v

# Run specific test category
python -m pytest -m auth -v

# Run all tests
python -m pytest -v

# Run with coverage
python -m pytest --cov=app --cov-report=html
```

### Do NOT use system pytest

❌ **This will fail**:
```bash
pytest tests/test_example.py  # Missing dependencies
```

✅ **This will work**:
```bash
source venv/bin/activate
python -m pytest tests/test_example.py
```

## Test Results

### Passing Tests (✅)
- **test_example.py**: All 3 tests pass
- **test_auth.py**: All 13 tests pass
- **test_league.py**: 15 out of 20 tests pass

### Tests Needing Minor Fixes
- **test_league.py**: 5 tests have off-by-one errors in membership counting
- **test_draft.py**: Need to update Pokemon tests for species relationships
- **test_pokemon.py**: Need to update tests for actual Pokemon/Species model structure

## Next Steps

1. **Fix remaining League tests**: Update logic for counting league memberships (owner needs explicit membership record)

2. **Update Pokemon tests**: The Pokemon model is more complex than initially assumed, with relationships to Species. Tests need to be updated to either:
   - Test at the Species level for legendary/mythical/generation filters
   - Or use helper methods that query through relationships

3. **Add more test coverage**: Continue adding tests for:
   - Season management
   - Team management
   - Trade functionality
   - Match/Tournament brackets
   - WebSocket connections

## Model Field Reference

Quick reference for correct field names:

| Model | Field Name | Type |
|-------|------------|------|
| User | discord_id | str |
| User | discord_username | str |
| Draft | budget_per_team | int |
| Draft | session_token | str |
| Draft | creator_id | UUID |
| Pokemon | identifier | str |
| Pokemon | species_id | int |
| LeagueMembership | is_active | bool |

## Helper Commands

```bash
# Find all instances of a field name in tests
grep -r "discord_user_id" tests/

# Replace a field name globally (use with caution!)
sed -i '' 's/old_name/new_name/g' tests/integration/test_file.py

# Run only failed tests from last run
python -m pytest --lf -v

# Run tests in parallel (faster)
python -m pytest -n auto
```
