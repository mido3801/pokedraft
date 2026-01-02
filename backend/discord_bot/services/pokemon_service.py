"""Pokemon service for Discord bot operations."""
from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Pokemon, PokemonType, Team, TeamPokemon


class PokemonService:
    """Service for Pokemon-related operations in the Discord bot."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pokemon_by_id(self, pokemon_id: int) -> Optional[Pokemon]:
        """Get a Pokemon by its ID.

        Args:
            pokemon_id: The PokeAPI Pokemon ID.

        Returns:
            The Pokemon if found, None otherwise.
        """
        result = await self.db.execute(
            select(Pokemon)
            .where(Pokemon.id == pokemon_id)
            .options(
                selectinload(Pokemon.types).selectinload("type"),
                selectinload(Pokemon.stats).selectinload("stat"),
                selectinload(Pokemon.abilities).selectinload("ability"),
            )
        )
        return result.scalar_one_or_none()

    async def search_pokemon(
        self,
        query: str,
        limit: int = 25,
        type_filter: Optional[str] = None,
        generation_filter: Optional[int] = None,
    ) -> list[Pokemon]:
        """Search for Pokemon by name.

        Args:
            query: Search query (matches against identifier).
            limit: Maximum results to return.
            type_filter: Optional type to filter by.
            generation_filter: Optional generation to filter by.

        Returns:
            List of matching Pokemon.
        """
        stmt = select(Pokemon).where(Pokemon.identifier.ilike(f"%{query}%"))

        if generation_filter:
            stmt = stmt.where(Pokemon.generation == generation_filter)

        stmt = stmt.options(
            selectinload(Pokemon.types).selectinload("type"),
        ).order_by(Pokemon.id).limit(limit)

        result = await self.db.execute(stmt)
        pokemon_list = list(result.scalars().all())

        # Filter by type if specified
        if type_filter:
            type_filter_lower = type_filter.lower()
            pokemon_list = [
                p for p in pokemon_list
                if any(
                    t.type.identifier == type_filter_lower
                    for t in p.types
                )
            ]

        return pokemon_list

    async def get_pokemon_by_name(self, name: str) -> Optional[Pokemon]:
        """Get a Pokemon by its name (identifier).

        Args:
            name: The Pokemon name/identifier.

        Returns:
            The Pokemon if found, None otherwise.
        """
        result = await self.db.execute(
            select(Pokemon)
            .where(Pokemon.identifier == name.lower())
            .options(
                selectinload(Pokemon.types).selectinload("type"),
                selectinload(Pokemon.stats).selectinload("stat"),
                selectinload(Pokemon.abilities).selectinload("ability"),
            )
        )
        return result.scalar_one_or_none()

    async def get_team_roster(self, team_id: str) -> list[tuple[TeamPokemon, Pokemon]]:
        """Get a team's roster with Pokemon details.

        Args:
            team_id: The team ID.

        Returns:
            List of (TeamPokemon, Pokemon) tuples.
        """
        import uuid
        team_uuid = uuid.UUID(team_id)

        result = await self.db.execute(
            select(TeamPokemon)
            .where(TeamPokemon.team_id == team_uuid)
            .order_by(TeamPokemon.acquired_at)
        )
        team_pokemon = list(result.scalars().all())

        roster = []
        for tp in team_pokemon:
            pokemon = await self.get_pokemon_by_id(tp.pokemon_id)
            if pokemon:
                roster.append((tp, pokemon))

        return roster

    async def get_all_types(self) -> list[PokemonType]:
        """Get all Pokemon types.

        Returns:
            List of all PokemonType entries.
        """
        result = await self.db.execute(
            select(PokemonType).order_by(PokemonType.id)
        )
        return list(result.scalars().all())

    def format_pokemon_types(self, pokemon: Pokemon) -> str:
        """Format a Pokemon's types as a string.

        Args:
            pokemon: The Pokemon object.

        Returns:
            Formatted types string (e.g., "Fire/Flying").
        """
        types = sorted(pokemon.types, key=lambda t: t.slot)
        return "/".join(t.type.identifier.title() for t in types)

    def format_pokemon_stats(self, pokemon: Pokemon) -> dict[str, int]:
        """Format a Pokemon's stats as a dictionary.

        Args:
            pokemon: The Pokemon object.

        Returns:
            Dict mapping stat name to value.
        """
        stat_names = {
            1: "HP",
            2: "Atk",
            3: "Def",
            4: "SpA",
            5: "SpD",
            6: "Spe",
        }
        return {
            stat_names.get(s.stat_id, s.stat.identifier): s.base_stat
            for s in pokemon.stats
        }

    def format_pokemon_abilities(self, pokemon: Pokemon) -> list[str]:
        """Format a Pokemon's abilities.

        Args:
            pokemon: The Pokemon object.

        Returns:
            List of ability names (hidden abilities marked).
        """
        abilities = []
        for a in sorted(pokemon.abilities, key=lambda x: x.slot):
            name = a.ability.identifier.replace("-", " ").title()
            if a.is_hidden:
                name += " (HA)"
            abilities.append(name)
        return abilities

    async def get_pokemon_autocomplete(
        self, current: str, limit: int = 25
    ) -> list[tuple[str, str]]:
        """Get Pokemon for autocomplete.

        Args:
            current: Current input text.
            limit: Max results.

        Returns:
            List of (display_name, identifier) tuples.
        """
        if not current:
            # Return popular Pokemon if no input
            result = await self.db.execute(
                select(Pokemon)
                .where(Pokemon.is_default == True)
                .order_by(Pokemon.id)
                .limit(limit)
            )
        else:
            result = await self.db.execute(
                select(Pokemon)
                .where(
                    or_(
                        Pokemon.identifier.ilike(f"{current}%"),
                        Pokemon.identifier.ilike(f"%{current}%"),
                    )
                )
                .where(Pokemon.is_default == True)
                .order_by(
                    # Prioritize exact starts
                    Pokemon.identifier.ilike(f"{current}%").desc(),
                    Pokemon.id,
                )
                .limit(limit)
            )

        pokemon_list = result.scalars().all()
        return [(p.name, p.identifier) for p in pokemon_list]
