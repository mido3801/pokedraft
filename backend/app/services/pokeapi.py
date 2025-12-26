"""
Service for fetching Pokemon data from the local database.

This replaces the previous HTTP-based service that called the external PokeAPI.
Data is now loaded from CSV files into PostgreSQL for faster, offline access.
"""

from typing import Optional, Dict, List, Set

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pokemon import (
    Pokemon,
    PokemonSpecies,
    PokemonType,
    PokemonTypeLink,
    PokemonStatValue,
    PokemonAbilityLink,
)
from app.services.sprites import get_sprite_url, SpriteStyle


async def _build_evolution_map(db: AsyncSession) -> Dict[int, int]:
    """
    Build a map of species_id -> evolution_stage.

    Evolution stages:
    - 0: Unevolved (baby/basic Pokemon with no pre-evolution)
    - 1: Middle stage (has a pre-evolution and can evolve further)
    - 2: Fully evolved (has a pre-evolution but cannot evolve)

    For Pokemon that don't evolve at all, they're considered stage 2 (fully evolved).
    """
    # Get all species with their evolution relationships
    stmt = select(PokemonSpecies.id, PokemonSpecies.evolves_from_species_id)
    result = await db.execute(stmt)
    species_data = result.all()

    # Build parent->children map and track which species have pre-evolutions
    has_pre_evo: Set[int] = set()
    children_map: Dict[int, List[int]] = {}

    for species_id, evolves_from in species_data:
        if evolves_from is not None:
            has_pre_evo.add(species_id)
            if evolves_from not in children_map:
                children_map[evolves_from] = []
            children_map[evolves_from].append(species_id)

    # Determine evolution stage for each species
    evolution_map: Dict[int, int] = {}

    for species_id, evolves_from in species_data:
        has_children = species_id in children_map
        has_parent = species_id in has_pre_evo

        if not has_parent and not has_children:
            # Single-stage Pokemon (no evolutions) - consider fully evolved
            evolution_map[species_id] = 2
        elif not has_parent and has_children:
            # Basic Pokemon that can evolve
            evolution_map[species_id] = 0
        elif has_parent and has_children:
            # Middle stage
            evolution_map[species_id] = 1
        else:
            # has_parent and not has_children - fully evolved
            evolution_map[species_id] = 2

    return evolution_map


class PokeAPIService:
    """
    Service for fetching Pokemon data from the local database.

    Provides the same interface as the previous HTTP-based service
    but queries the local PostgreSQL database instead.
    """

    def _format_pokemon(
        self,
        pokemon: Pokemon,
        sprite_style: SpriteStyle | str | None = None,
        evolution_map: Dict[int, int] | None = None,
    ) -> dict:
        """Format a Pokemon model instance to API response dict."""
        # Get types sorted by slot
        types = sorted(pokemon.types, key=lambda t: t.slot)
        type_names = [t.type.identifier for t in types]

        # Get stats as dict
        stats = {sv.stat.identifier: sv.base_stat for sv in pokemon.stats}

        # Calculate base stat total
        bst = sum(stats.values())

        # Get non-hidden abilities sorted by slot
        abilities = sorted(
            [a for a in pokemon.abilities if not a.is_hidden],
            key=lambda a: a.slot
        )
        ability_names = [a.ability.identifier for a in abilities]

        # Get species info
        species = pokemon.species
        generation = species.generation_id if species else None
        is_legendary = species.is_legendary if species else False
        is_mythical = species.is_mythical if species else False

        # Get evolution stage from map if provided
        evolution_stage = None
        if evolution_map and species:
            evolution_stage = evolution_map.get(species.id, 2)

        return {
            "id": pokemon.id,
            "name": pokemon.identifier,
            "types": type_names,
            "sprite": get_sprite_url(pokemon.id, sprite_style),
            "stats": stats,
            "bst": bst,
            "abilities": ability_names,
            "generation": generation,
            "is_legendary": is_legendary,
            "is_mythical": is_mythical,
            "evolution_stage": evolution_stage,
        }

    async def get_pokemon(
        self,
        pokemon_id: int,
        db: AsyncSession,
        sprite_style: SpriteStyle | str | None = None,
    ) -> Optional[dict]:
        """Get Pokemon data by ID."""
        stmt = (
            select(Pokemon)
            .options(
                selectinload(Pokemon.species),
                selectinload(Pokemon.types).selectinload(PokemonTypeLink.type),
                selectinload(Pokemon.stats).selectinload(PokemonStatValue.stat),
                selectinload(Pokemon.abilities).selectinload(PokemonAbilityLink.ability),
            )
            .where(Pokemon.id == pokemon_id)
        )

        result = await db.execute(stmt)
        pokemon = result.scalar_one_or_none()

        if not pokemon:
            return None

        return self._format_pokemon(pokemon, sprite_style)

    async def get_pokemon_by_name(
        self,
        name: str,
        db: AsyncSession,
        sprite_style: SpriteStyle | str | None = None,
    ) -> Optional[dict]:
        """Get Pokemon data by name."""
        stmt = (
            select(Pokemon)
            .options(
                selectinload(Pokemon.species),
                selectinload(Pokemon.types).selectinload(PokemonTypeLink.type),
                selectinload(Pokemon.stats).selectinload(PokemonStatValue.stat),
                selectinload(Pokemon.abilities).selectinload(PokemonAbilityLink.ability),
            )
            .where(Pokemon.identifier == name.lower())
        )

        result = await db.execute(stmt)
        pokemon = result.scalar_one_or_none()

        if not pokemon:
            return None

        return self._format_pokemon(pokemon, sprite_style)

    async def get_generation_pokemon(
        self,
        generation: int,
        db: AsyncSession,
    ) -> List[dict]:
        """Get all Pokemon from a specific generation."""
        stmt = (
            select(Pokemon)
            .join(PokemonSpecies)
            .where(PokemonSpecies.generation_id == generation)
            .where(Pokemon.is_default == True)
            .order_by(Pokemon.id)
        )

        result = await db.execute(stmt)
        pokemon_list = result.scalars().all()

        return [
            {"id": p.id, "name": p.identifier}
            for p in pokemon_list
        ]

    async def validate_pokemon_ids(
        self,
        pokemon_ids: List[int],
        db: AsyncSession,
    ) -> Dict[int, bool]:
        """Validate that a list of Pokemon IDs exist in the database."""
        if not pokemon_ids:
            return {}

        stmt = select(Pokemon.id).where(Pokemon.id.in_(pokemon_ids))
        result = await db.execute(stmt)
        valid_ids = set(result.scalars().all())

        return {pid: pid in valid_ids for pid in pokemon_ids}

    async def search_pokemon(
        self,
        db: AsyncSession,
        query: str | None = None,
        type_filter: str | None = None,
        generation: int | None = None,
        is_legendary: bool | None = None,
        is_mythical: bool | None = None,
        limit: int = 100,
        offset: int = 0,
        sprite_style: SpriteStyle | str | None = None,
    ) -> List[dict]:
        """
        Search Pokemon with filters.

        Args:
            db: Database session
            query: Search term for Pokemon name (partial match)
            type_filter: Filter by type identifier (e.g., "fire", "water")
            generation: Filter by generation number
            is_legendary: Filter for legendary Pokemon
            is_mythical: Filter for mythical Pokemon
            limit: Maximum results to return
            offset: Number of results to skip
            sprite_style: Sprite style for returned Pokemon

        Returns:
            List of Pokemon data dictionaries
        """
        stmt = (
            select(Pokemon)
            .join(PokemonSpecies)
            .options(
                selectinload(Pokemon.species),
                selectinload(Pokemon.types).selectinload(PokemonTypeLink.type),
                selectinload(Pokemon.stats).selectinload(PokemonStatValue.stat),
                selectinload(Pokemon.abilities).selectinload(PokemonAbilityLink.ability),
            )
            .where(Pokemon.is_default == True)
        )

        # Apply filters
        if query:
            stmt = stmt.where(Pokemon.identifier.ilike(f"%{query}%"))

        if type_filter:
            stmt = stmt.join(PokemonTypeLink).join(PokemonType).where(
                PokemonType.identifier == type_filter.lower()
            )

        if generation is not None:
            stmt = stmt.where(PokemonSpecies.generation_id == generation)

        if is_legendary is not None:
            stmt = stmt.where(PokemonSpecies.is_legendary == is_legendary)

        if is_mythical is not None:
            stmt = stmt.where(PokemonSpecies.is_mythical == is_mythical)

        # Order and paginate
        stmt = stmt.order_by(Pokemon.id).offset(offset).limit(limit)

        result = await db.execute(stmt)
        pokemon_list = result.scalars().unique().all()

        return [self._format_pokemon(p, sprite_style) for p in pokemon_list]

    async def get_all_pokemon(
        self,
        db: AsyncSession,
        sprite_style: SpriteStyle | str | None = None,
        limit: int | None = None,
        include_evolution_stage: bool = False,
    ) -> List[dict]:
        """Get all Pokemon (default forms only)."""
        stmt = (
            select(Pokemon)
            .join(PokemonSpecies)
            .options(
                selectinload(Pokemon.species),
                selectinload(Pokemon.types).selectinload(PokemonTypeLink.type),
                selectinload(Pokemon.stats).selectinload(PokemonStatValue.stat),
                selectinload(Pokemon.abilities).selectinload(PokemonAbilityLink.ability),
            )
            .where(Pokemon.is_default == True)
            .order_by(Pokemon.id)
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        pokemon_list = result.scalars().all()

        # Build evolution map if requested
        evolution_map = None
        if include_evolution_stage:
            evolution_map = await _build_evolution_map(db)

        return [self._format_pokemon(p, sprite_style, evolution_map) for p in pokemon_list]

    async def get_all_pokemon_for_box(
        self,
        db: AsyncSession,
        sprite_style: SpriteStyle | str | None = "default",
    ) -> List[dict]:
        """
        Get all Pokemon with full metadata for the Pokemon box display.

        Returns lightweight data optimized for the box view:
        - id, name, sprite, types, generation, bst, evolution_stage, is_legendary, is_mythical
        """
        # Build evolution map first
        evolution_map = await _build_evolution_map(db)

        stmt = (
            select(Pokemon)
            .join(PokemonSpecies)
            .options(
                selectinload(Pokemon.species),
                selectinload(Pokemon.types).selectinload(PokemonTypeLink.type),
                selectinload(Pokemon.stats).selectinload(PokemonStatValue.stat),
            )
            .where(Pokemon.is_default == True)
            .order_by(Pokemon.id)
        )

        result = await db.execute(stmt)
        pokemon_list = result.scalars().all()

        # Return optimized data for box display
        box_data = []
        for p in pokemon_list:
            types = sorted(p.types, key=lambda t: t.slot)
            type_names = [t.type.identifier for t in types]
            stats = {sv.stat.identifier: sv.base_stat for sv in p.stats}
            bst = sum(stats.values())

            species = p.species
            evolution_stage = evolution_map.get(species.id, 2) if species else 2

            box_data.append({
                "id": p.id,
                "name": p.identifier,
                "sprite": get_sprite_url(p.id, sprite_style),
                "types": type_names,
                "generation": species.generation_id if species else None,
                "bst": bst,
                "evolution_stage": evolution_stage,
                "is_legendary": species.is_legendary if species else False,
                "is_mythical": species.is_mythical if species else False,
            })

        return box_data

    async def get_pokemon_count(self, db: AsyncSession) -> int:
        """Get total count of Pokemon in database."""
        stmt = select(func.count()).select_from(Pokemon).where(Pokemon.is_default == True)
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def get_types(self, db: AsyncSession) -> List[dict]:
        """Get all Pokemon types."""
        stmt = select(PokemonType).order_by(PokemonType.id)
        result = await db.execute(stmt)
        types = result.scalars().all()

        return [
            {"id": t.id, "name": t.identifier}
            for t in types
        ]


# Singleton instance
pokeapi_service = PokeAPIService()
