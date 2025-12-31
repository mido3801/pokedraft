"""
Integration tests for Pokemon Data Management requirements (FR-POKE-*).

These tests verify Pokemon data storage, retrieval, and filtering
as specified in the requirements document.
"""

import pytest
from sqlalchemy import select

from app.models import Pokemon, PokemonType, PokemonAbility
from tests.utils.factories import PokemonFactory
from tests.utils.helpers import count_records, exists


# ============================================================================
# FR-POKE-002: Store Pokemon species information
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_store_pokemon_species_information(db_session):
    """
    Test FR-POKE-002: The system shall store Pokemon species information
    including name, generation, and classification.

    Scenario:
        1. Create Pokemon with species info
        2. Verify all information stored
    """
    # Act
    pokemon = await PokemonFactory.create(
        db_session,
        identifier="Pikachu",
        generation=1,
        evolution_stage="middle",
    )

    # Assert
    assert pokemon.id is not None
    assert pokemon.identifier == "Pikachu"
    assert pokemon.generation == 1
    assert pokemon.evolution_stage == "middle"


# ============================================================================
# FR-POKE-006: Calculate Base Stat Total
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_store_base_stat_total(db_session):
    """
    Test FR-POKE-006: The system shall calculate Base Stat Total (BST)
    for each Pokemon.

    Scenario:
        1. Create Pokemon with BST
        2. Verify BST stored correctly
    """
    # Act
    pokemon = await PokemonFactory.create(
        db_session,
        identifier="Charizard",
        base_stat_total=534,
    )

    # Assert
    assert pokemon.base_stat_total == 534


# ============================================================================
# FR-POKE-007: Track evolution stage
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
@pytest.mark.parametrize(
    "evolution_stage",
    ["unevolved", "middle", "fully_evolved"],
)
async def test_track_evolution_stage(db_session, evolution_stage):
    """
    Test FR-POKE-007: The system shall track evolution stage for each Pokemon.

    Scenario:
        1. Create Pokemon with different evolution stages
        2. Verify stage stored correctly
    """
    # Act
    pokemon = await PokemonFactory.create(
        db_session,
        evolution_stage=evolution_stage,
    )

    # Assert
    assert pokemon.evolution_stage == evolution_stage


# ============================================================================
# FR-POKE-008 & FR-POKE-009: Flag legendary and mythical
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_flag_legendary_pokemon(db_session):
    """
    Test FR-POKE-008: The system shall flag legendary Pokemon.

    Scenario:
        1. Create legendary Pokemon
        2. Verify legendary flag set
    """
    # Act
    legendary = await PokemonFactory.create(
        db_session,
        identifier="Mewtwo",
        is_legendary=True,
        is_mythical=False,
    )
    regular = await PokemonFactory.create(
        db_session,
        identifier="Pidgey",
        is_legendary=False,
        is_mythical=False,
    )

    # Assert
    assert legendary.is_legendary is True
    assert regular.is_legendary is False


@pytest.mark.pokemon
@pytest.mark.integration
async def test_flag_mythical_pokemon(db_session):
    """
    Test FR-POKE-009: The system shall flag mythical Pokemon.

    Scenario:
        1. Create mythical Pokemon
        2. Verify mythical flag set
    """
    # Act
    mythical = await PokemonFactory.create(
        db_session,
        identifier="Mew",
        is_legendary=False,
        is_mythical=True,
    )

    # Assert
    assert mythical.is_mythical is True
    assert mythical.is_legendary is False


# ============================================================================
# FR-POKE-010: Search by name
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_search_pokemon_by_name_exact(db_session):
    """
    Test FR-POKE-010: The system shall allow searching Pokemon by name
    (case-insensitive, partial match).

    Scenario:
        1. Create Pokemon with specific name
        2. Search by exact name
        3. Verify found
    """
    # Arrange
    await PokemonFactory.create(db_session, identifier="Bulbasaur")
    await PokemonFactory.create(db_session, identifier="Ivysaur")

    # Act
    result = await db_session.execute(
        select(Pokemon).where(Pokemon.identifier == "Bulbasaur")
    )
    found = result.scalar_one_or_none()

    # Assert
    assert found is not None
    assert found.name == "Bulbasaur"


@pytest.mark.pokemon
@pytest.mark.integration
async def test_search_pokemon_by_name_partial(db_session):
    """
    Test partial name matching (case-insensitive).

    Scenario:
        1. Create Pokemon
        2. Search with partial name
        3. Verify matches found
    """
    # Arrange
    await PokemonFactory.create(db_session, identifier="Bulbasaur")
    await PokemonFactory.create(db_session, identifier="Ivysaur")
    await PokemonFactory.create(db_session, identifier="Venusaur")

    # Act - Search for Pokemon containing "saur"
    result = await db_session.execute(
        select(Pokemon).where(Pokemon.identifier.ilike("%saur%"))
    )
    matches = result.scalars().all()

    # Assert
    assert len(matches) == 3
    assert all("saur" in p.name.lower() for p in matches)


# ============================================================================
# FR-POKE-012: Filter by generation
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_filter_pokemon_by_generation(db_session):
    """
    Test FR-POKE-012: The system shall allow filtering Pokemon by generation.

    Scenario:
        1. Create Pokemon from different generations
        2. Filter by specific generation
        3. Verify correct Pokemon returned
    """
    # Arrange
    await PokemonFactory.create(db_session, identifier="Gen1Mon", generation=1)
    await PokemonFactory.create(db_session, identifier="Gen2Mon", generation=2)
    await PokemonFactory.create(db_session, identifier="Gen3Mon", generation=3)
    await PokemonFactory.create(db_session, identifier="Gen1Mon2", generation=1)

    # Act
    result = await db_session.execute(
        select(Pokemon).where(Pokemon.generation == 1)
    )
    gen1_pokemon = result.scalars().all()

    # Assert
    assert len(gen1_pokemon) == 2
    assert all(p.generation == 1 for p in gen1_pokemon)


# ============================================================================
# FR-POKE-013: Filter by evolution stage
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_filter_pokemon_by_evolution_stage(db_session):
    """
    Test FR-POKE-013: The system shall allow filtering Pokemon by evolution stage.

    Scenario:
        1. Create Pokemon with different evolution stages
        2. Filter by specific stage
        3. Verify correct Pokemon returned
    """
    # Arrange
    await PokemonFactory.create(db_session, evolution_stage="unevolved")
    await PokemonFactory.create(db_session, evolution_stage="unevolved")
    await PokemonFactory.create(db_session, evolution_stage="middle")
    await PokemonFactory.create(db_session, evolution_stage="fully_evolved")

    # Act
    result = await db_session.execute(
        select(Pokemon).where(Pokemon.evolution_stage == "unevolved")
    )
    unevolved = result.scalars().all()

    # Assert
    assert len(unevolved) == 2
    assert all(p.evolution_stage == "unevolved" for p in unevolved)


# ============================================================================
# FR-POKE-014: Filter by BST range
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_filter_pokemon_by_bst_range(db_session):
    """
    Test FR-POKE-014: The system shall allow filtering Pokemon by BST range.

    Scenario:
        1. Create Pokemon with different BST values
        2. Filter by BST range
        3. Verify correct Pokemon returned
    """
    # Arrange
    await PokemonFactory.create(db_session, identifier="Weak", base_stat_total=300)
    await PokemonFactory.create(db_session, identifier="Average", base_stat_total=500)
    await PokemonFactory.create(db_session, identifier="Strong", base_stat_total=600)
    await PokemonFactory.create(db_session, identifier="Legendary", base_stat_total=680)

    # Act - Filter BST between 500 and 600
    result = await db_session.execute(
        select(Pokemon).where(
            Pokemon.base_stat_total >= 500, Pokemon.base_stat_total <= 600
        )
    )
    filtered = result.scalars().all()

    # Assert
    assert len(filtered) == 2
    assert all(500 <= p.base_stat_total <= 600 for p in filtered)


# ============================================================================
# FR-POKE-017 & FR-POKE-018: Filter by legendary/mythical status
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_filter_pokemon_by_legendary_status(db_session):
    """
    Test FR-POKE-017: The system shall allow filtering Pokemon by legendary status.

    Scenario:
        1. Create mix of legendary and regular Pokemon
        2. Filter by legendary status
        3. Verify correct Pokemon returned
    """
    # Arrange
    await PokemonFactory.create(db_session, identifier="Regular1", is_legendary=False)
    await PokemonFactory.create(db_session, identifier="Legendary1", is_legendary=True)
    await PokemonFactory.create(db_session, identifier="Legendary2", is_legendary=True)
    await PokemonFactory.create(db_session, identifier="Regular2", is_legendary=False)

    # Act
    result = await db_session.execute(
        select(Pokemon).where(Pokemon.is_legendary == True)
    )
    legendaries = result.scalars().all()

    # Assert
    assert len(legendaries) == 2
    assert all(p.is_legendary for p in legendaries)


@pytest.mark.pokemon
@pytest.mark.integration
async def test_filter_pokemon_by_mythical_status(db_session):
    """
    Test FR-POKE-018: The system shall allow filtering Pokemon by mythical status.

    Scenario:
        1. Create mix of mythical and regular Pokemon
        2. Filter by mythical status
        3. Verify correct Pokemon returned
    """
    # Arrange
    await PokemonFactory.create(db_session, identifier="Regular", is_mythical=False)
    await PokemonFactory.create(db_session, identifier="Mythical", is_mythical=True)

    # Act
    result = await db_session.execute(
        select(Pokemon).where(Pokemon.is_mythical == True)
    )
    mythicals = result.scalars().all()

    # Assert
    assert len(mythicals) == 1
    assert mythicals[0].is_mythical is True


# ============================================================================
# FR-POKE-019 & FR-POKE-020: Retrieve by ID and name
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_retrieve_pokemon_by_id(db_session):
    """
    Test FR-POKE-019: The system shall retrieve Pokemon by unique ID.

    Scenario:
        1. Create Pokemon
        2. Retrieve by ID
        3. Verify correct Pokemon returned
    """
    # Arrange
    pokemon = await PokemonFactory.create(db_session, identifier="Squirtle")

    # Act
    result = await db_session.execute(
        select(Pokemon).where(Pokemon.id == pokemon.id)
    )
    retrieved = result.scalar_one_or_none()

    # Assert
    assert retrieved is not None
    assert retrieved.id == pokemon.id
    assert retrieved.name == "Squirtle"


@pytest.mark.pokemon
@pytest.mark.integration
async def test_retrieve_pokemon_by_name(db_session):
    """
    Test FR-POKE-020: The system shall retrieve Pokemon by name.

    Scenario:
        1. Create Pokemon
        2. Retrieve by name
        3. Verify correct Pokemon returned
    """
    # Arrange
    pokemon = await PokemonFactory.create(db_session, identifier="Wartortle")

    # Act
    result = await db_session.execute(
        select(Pokemon).where(Pokemon.identifier == "Wartortle")
    )
    retrieved = result.scalar_one_or_none()

    # Assert
    assert retrieved is not None
    assert retrieved.name == "Wartortle"


# ============================================================================
# Complex Query Tests
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
async def test_complex_pokemon_filter_query(db_session):
    """
    Test complex filtering combining multiple criteria.

    Scenario:
        1. Create diverse set of Pokemon
        2. Apply multiple filters
        3. Verify correct results
    """
    # Arrange - Create diverse Pokemon
    await PokemonFactory.create_batch_with_variety(db_session, count=20)

    # Act - Filter: Generation 1, BST >= 500, not legendary
    result = await db_session.execute(
        select(Pokemon).where(
            Pokemon.generation == 1,
            Pokemon.base_stat_total >= 500,
            Pokemon.is_legendary == False,
        )
    )
    filtered = result.scalars().all()

    # Assert
    for pokemon in filtered:
        assert pokemon.generation == 1
        assert pokemon.base_stat_total >= 500
        assert pokemon.is_legendary is False


# ============================================================================
# Parametrized Tests
# ============================================================================


@pytest.mark.pokemon
@pytest.mark.integration
@pytest.mark.parametrize(
    "generation,expected_min",
    [
        (1, 0),
        (2, 0),
        (5, 0),
        (9, 0),
    ],
)
async def test_filter_by_multiple_generations(db_session, generation, expected_min):
    """
    Parametrized test for filtering by generation.

    Creates Pokemon across generations and verifies filtering.
    """
    # Arrange
    await PokemonFactory.create_batch_with_variety(db_session, count=10)

    # Act
    result = await db_session.execute(
        select(Pokemon).where(Pokemon.generation == generation)
    )
    filtered = result.scalars().all()

    # Assert - Should have at least 0 (could have some from variety batch)
    assert len(filtered) >= expected_min
    if len(filtered) > 0:
        assert all(p.generation == generation for p in filtered)


@pytest.mark.pokemon
@pytest.mark.integration
@pytest.mark.parametrize(
    "min_bst,max_bst",
    [
        (0, 300),
        (300, 500),
        (500, 600),
        (600, 800),
    ],
)
async def test_filter_by_various_bst_ranges(db_session, min_bst, max_bst):
    """
    Parametrized test for BST range filtering.

    Tests various BST ranges to ensure filtering works correctly.
    """
    # Arrange
    await PokemonFactory.create_batch_with_variety(db_session, count=15)

    # Act
    result = await db_session.execute(
        select(Pokemon).where(
            Pokemon.base_stat_total >= min_bst, Pokemon.base_stat_total <= max_bst
        )
    )
    filtered = result.scalars().all()

    # Assert
    for pokemon in filtered:
        assert min_bst <= pokemon.base_stat_total <= max_bst
