"""Pokemon lookup commands for Discord bot."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from discord_bot.cogs.base import BaseCog
from discord_bot.config import Colors, get_pokemon_sprite
from discord_bot.database import get_db_session
from discord_bot.services.pokemon_service import PokemonService


class PokemonCommands(BaseCog):
    """Commands for looking up Pokemon information."""

    pokemon_group = app_commands.Group(
        name="pokemon",
        description="Look up Pokemon information",
    )

    @pokemon_group.command(name="info", description="Get detailed info about a Pokemon")
    @app_commands.describe(pokemon="The Pokemon to look up")
    async def info(self, interaction: discord.Interaction, pokemon: str):
        """Show detailed information about a Pokemon."""
        async with get_db_session() as db:
            pokemon_service = PokemonService(db)

            # Try to find by name
            pkmn = await pokemon_service.get_pokemon_by_name(pokemon.lower())

            if not pkmn:
                # Try to parse as ID
                try:
                    pokemon_id = int(pokemon)
                    pkmn = await pokemon_service.get_pokemon_by_id(pokemon_id)
                except ValueError:
                    pass

            if not pkmn:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Pokemon Not Found",
                        f"Could not find a Pokemon matching '{pokemon}'.\n"
                        "Try using the autocomplete suggestions.",
                    ),
                    ephemeral=True,
                )
                return

            # Build the info embed
            types = pokemon_service.format_pokemon_types(pkmn)
            stats = pokemon_service.format_pokemon_stats(pkmn)
            abilities = pokemon_service.format_pokemon_abilities(pkmn)

            embed = discord.Embed(
                title=f"#{pkmn.id} {pkmn.name}",
                description=f"**Type:** {types}",
                color=Colors.POKEMON,
            )

            # Stats
            stats_text = "\n".join(f"**{name}:** {value}" for name, value in stats.items())
            stats_text += f"\n**BST:** {pkmn.base_stat_total}"
            embed.add_field(name="Base Stats", value=stats_text, inline=True)

            # Additional info
            info_text = f"**Generation:** {pkmn.generation}\n"
            info_text += f"**Evolution Stage:** {pkmn.evolution_stage.title()}\n"
            info_text += f"**Height:** {pkmn.height / 10}m\n"
            info_text += f"**Weight:** {pkmn.weight / 10}kg"

            if pkmn.is_legendary:
                info_text += "\n**Legendary**"
            if pkmn.is_mythical:
                info_text += "\n**Mythical**"

            embed.add_field(name="Info", value=info_text, inline=True)

            # Abilities
            embed.add_field(
                name="Abilities",
                value="\n".join(abilities) or "None",
                inline=False,
            )

            # Set thumbnail
            embed.set_thumbnail(url=get_pokemon_sprite(pkmn.id))

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @pokemon_group.command(name="search", description="Search for Pokemon")
    @app_commands.describe(
        query="Search by name",
        type="Filter by type",
        generation="Filter by generation (1-9)",
    )
    async def search(
        self,
        interaction: discord.Interaction,
        query: str,
        type: Optional[str] = None,
        generation: Optional[int] = None,
    ):
        """Search for Pokemon matching criteria."""
        async with get_db_session() as db:
            pokemon_service = PokemonService(db)

            results = await pokemon_service.search_pokemon(
                query=query,
                limit=25,
                type_filter=type,
                generation_filter=generation,
            )

            if not results:
                filters = []
                if type:
                    filters.append(f"type={type}")
                if generation:
                    filters.append(f"gen={generation}")
                filter_text = f" ({', '.join(filters)})" if filters else ""

                await interaction.response.send_message(
                    embed=self.info_embed(
                        "No Results",
                        f"No Pokemon found matching '{query}'{filter_text}.",
                    ),
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title=f"Search Results: '{query}'",
                color=Colors.POKEMON,
            )

            # Add filter info
            filter_parts = []
            if type:
                filter_parts.append(f"Type: {type.title()}")
            if generation:
                filter_parts.append(f"Generation: {generation}")
            if filter_parts:
                embed.description = " | ".join(filter_parts)

            # Format results
            result_lines = []
            for pkmn in results[:15]:
                types = pokemon_service.format_pokemon_types(pkmn)
                result_lines.append(
                    f"**#{pkmn.id} {pkmn.name}** - {types} (BST: {pkmn.base_stat_total})"
                )

            embed.add_field(
                name=f"Found {len(results)} Pokemon",
                value="\n".join(result_lines),
                inline=False,
            )

            if len(results) > 15:
                embed.set_footer(text=f"Showing 15 of {len(results)} results")

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @pokemon_group.command(name="compare", description="Compare two Pokemon")
    @app_commands.describe(
        pokemon1="First Pokemon",
        pokemon2="Second Pokemon",
    )
    async def compare(
        self,
        interaction: discord.Interaction,
        pokemon1: str,
        pokemon2: str,
    ):
        """Compare two Pokemon side by side."""
        async with get_db_session() as db:
            pokemon_service = PokemonService(db)

            pkmn1 = await pokemon_service.get_pokemon_by_name(pokemon1.lower())
            pkmn2 = await pokemon_service.get_pokemon_by_name(pokemon2.lower())

            errors = []
            if not pkmn1:
                errors.append(f"Could not find '{pokemon1}'")
            if not pkmn2:
                errors.append(f"Could not find '{pokemon2}'")

            if errors:
                await interaction.response.send_message(
                    embed=self.error_embed("Pokemon Not Found", "\n".join(errors)),
                    ephemeral=True,
                )
                return

            stats1 = pokemon_service.format_pokemon_stats(pkmn1)
            stats2 = pokemon_service.format_pokemon_stats(pkmn2)

            embed = discord.Embed(
                title=f"{pkmn1.name} vs {pkmn2.name}",
                color=Colors.POKEMON,
            )

            # Types
            types1 = pokemon_service.format_pokemon_types(pkmn1)
            types2 = pokemon_service.format_pokemon_types(pkmn2)
            embed.add_field(name=pkmn1.name, value=f"**Type:** {types1}", inline=True)
            embed.add_field(name=pkmn2.name, value=f"**Type:** {types2}", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)  # Spacer

            # Stats comparison
            stat_comparison = []
            for stat_name in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]:
                val1 = stats1.get(stat_name, 0)
                val2 = stats2.get(stat_name, 0)
                diff = val1 - val2
                if diff > 0:
                    indicator = f"+{diff}"
                elif diff < 0:
                    indicator = str(diff)
                else:
                    indicator = "="
                stat_comparison.append(f"**{stat_name}:** {val1} vs {val2} ({indicator})")

            embed.add_field(
                name="Stats Comparison",
                value="\n".join(stat_comparison),
                inline=False,
            )

            # BST
            bst_diff = pkmn1.base_stat_total - pkmn2.base_stat_total
            bst_indicator = f"+{bst_diff}" if bst_diff > 0 else str(bst_diff) if bst_diff < 0 else "="
            embed.add_field(
                name="Base Stat Total",
                value=f"{pkmn1.base_stat_total} vs {pkmn2.base_stat_total} ({bst_indicator})",
                inline=False,
            )

            # Set thumbnail to first Pokemon
            embed.set_thumbnail(url=get_pokemon_sprite(pkmn1.id))

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @info.autocomplete("pokemon")
    @compare.autocomplete("pokemon1")
    @compare.autocomplete("pokemon2")
    async def pokemon_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for Pokemon names."""
        async with get_db_session() as db:
            pokemon_service = PokemonService(db)
            results = await pokemon_service.get_pokemon_autocomplete(current)

            return [
                app_commands.Choice(name=display_name, value=identifier)
                for display_name, identifier in results
            ]

    @search.autocomplete("type")
    async def type_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for Pokemon types."""
        types = [
            "normal", "fire", "water", "electric", "grass", "ice",
            "fighting", "poison", "ground", "flying", "psychic", "bug",
            "rock", "ghost", "dragon", "dark", "steel", "fairy",
        ]

        if current:
            types = [t for t in types if current.lower() in t]

        return [
            app_commands.Choice(name=t.title(), value=t)
            for t in types[:25]
        ]


async def setup(bot: commands.Bot):
    """Set up the pokemon commands cog."""
    await bot.add_cog(PokemonCommands(bot))
