"""Team commands for Discord bot."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from discord_bot.cogs.base import BaseCog, LeagueContextMixin
from discord_bot.config import Colors, get_app_url, get_pokemon_sprite, Pagination
from discord_bot.database import get_db_session
from discord_bot.services.user_service import UserService
from discord_bot.services.league_service import LeagueService
from discord_bot.services.pokemon_service import PokemonService
from discord_bot.views.league_select import prompt_league_selection

from app.models import Team
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class TeamCommands(BaseCog, LeagueContextMixin):
    """Commands for viewing team information."""

    team_group = app_commands.Group(
        name="team",
        description="View team information",
    )

    @team_group.command(name="my", description="View your team's roster")
    @app_commands.describe(league="Select a league (optional)")
    async def my_team(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show the user's team roster."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Account Not Linked",
                        "Link your account with `/account link` first.",
                    ),
                    ephemeral=True,
                )
                return

            league_service = LeagueService(db)

            # Resolve league
            if league:
                target_league = await league_service.get_league_by_id(league)
            else:
                target_league = await self.resolve_league(
                    interaction, user_id=str(user.id)
                )

            if not target_league:
                leagues = await league_service.get_user_leagues(str(user.id))
                result = await prompt_league_selection(
                    interaction,
                    leagues,
                    title="Select League",
                    description="Which league's team do you want to view?",
                )
                if not result:
                    return
                target_league, new_interaction = result
                await self._show_user_team(
                    new_interaction, target_league, str(user.id), followup=True
                )
            else:
                await self._show_user_team(
                    interaction, target_league, str(user.id), followup=False
                )

    async def _show_user_team(
        self,
        interaction: discord.Interaction,
        league,
        user_id: str,
        followup: bool,
    ):
        """Display a user's team."""
        async with get_db_session() as db:
            league_service = LeagueService(db)
            team = await league_service.get_user_team_in_league(user_id, str(league.id))

            if not team:
                embed = self.info_embed(
                    "No Team Found",
                    f"You don't have a team in **{league.name}** yet.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            await self._show_team_roster(interaction, team, league, followup)

    @team_group.command(name="roster", description="View a team's roster")
    @app_commands.describe(
        team_name="The team name to look up",
        league="Select a league (optional)",
    )
    async def roster(
        self,
        interaction: discord.Interaction,
        team_name: str,
        league: Optional[str] = None,
    ):
        """Show a specific team's roster."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Account Not Linked",
                        "Link your account with `/account link` first.",
                    ),
                    ephemeral=True,
                )
                return

            league_service = LeagueService(db)

            # Resolve league
            if league:
                target_league = await league_service.get_league_by_id(league)
            else:
                target_league = await self.resolve_league(
                    interaction, user_id=str(user.id)
                )

            if not target_league:
                leagues = await league_service.get_user_leagues(str(user.id))
                result = await prompt_league_selection(
                    interaction,
                    leagues,
                    title="Select League",
                )
                if not result:
                    return
                target_league, new_interaction = result
                await self._find_and_show_team(
                    new_interaction, target_league, team_name, followup=True
                )
            else:
                await self._find_and_show_team(
                    interaction, target_league, team_name, followup=False
                )

    async def _find_and_show_team(
        self,
        interaction: discord.Interaction,
        league,
        team_name: str,
        followup: bool,
    ):
        """Find a team by name and show its roster."""
        async with get_db_session() as db:
            league_service = LeagueService(db)
            season = await league_service.get_active_season(str(league.id))

            if not season:
                embed = self.info_embed(
                    "No Active Season",
                    "There's no active season in this league.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Find the team by name
            result = await db.execute(
                select(Team)
                .where(Team.season_id == season.id)
                .where(Team.display_name.ilike(f"%{team_name}%"))
                .options(selectinload(Team.user), selectinload(Team.pokemon))
                .limit(1)
            )
            team = result.scalar_one_or_none()

            if not team:
                embed = self.error_embed(
                    "Team Not Found",
                    f"No team matching '{team_name}' found in {league.name}.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            await self._show_team_roster(interaction, team, league, followup)

    async def _show_team_roster(
        self,
        interaction: discord.Interaction,
        team: Team,
        league,
        followup: bool,
    ):
        """Display a team's roster."""
        async with get_db_session() as db:
            pokemon_service = PokemonService(db)
            roster = await pokemon_service.get_team_roster(str(team.id))

            owner_name = team.user.display_name if team.user else "Unknown"

            embed = discord.Embed(
                title=f"{team.display_name}",
                description=f"Owner: **{owner_name}**\nLeague: **{league.name}**",
                color=Colors.INFO,
            )

            # Record
            record = f"{team.wins}-{team.losses}"
            if team.ties > 0:
                record += f"-{team.ties}"
            embed.add_field(name="Record", value=record, inline=True)

            if team.budget_remaining is not None:
                embed.add_field(name="Budget", value=str(team.budget_remaining), inline=True)

            embed.add_field(name="Roster Size", value=str(len(roster)), inline=True)

            if roster:
                # Group Pokemon for display
                pokemon_lines = []
                for i, (team_pokemon, pokemon) in enumerate(roster[:12], 1):
                    types = pokemon_service.format_pokemon_types(pokemon)
                    pokemon_lines.append(f"**{pokemon.name}** ({types}) - BST: {pokemon.base_stat_total}")

                embed.add_field(
                    name="Pokemon",
                    value="\n".join(pokemon_lines) or "No Pokemon",
                    inline=False,
                )

                if len(roster) > 12:
                    embed.set_footer(text=f"Showing 12 of {len(roster)} Pokemon")

                # Set thumbnail to first Pokemon
                first_pokemon = roster[0][1]
                embed.set_thumbnail(url=get_pokemon_sprite(first_pokemon.id))
            else:
                embed.add_field(name="Pokemon", value="No Pokemon on roster", inline=False)

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @my_team.autocomplete("league")
    @roster.autocomplete("league")
    async def league_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for league parameter."""
        choices = await self.get_user_leagues_for_autocomplete(interaction)
        if current:
            choices = [c for c in choices if current.lower() in c.name.lower()]
        return choices[:25]

    @roster.autocomplete("team_name")
    async def team_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for team name."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))
            if not user:
                return []

            league_service = LeagueService(db)

            # Try to get the league from the interaction options
            league_id = None
            if interaction.data and "options" in interaction.data:
                for opt in interaction.data["options"]:
                    if opt.get("name") == "league":
                        league_id = opt.get("value")
                        break

            # Resolve league
            if league_id:
                target_league = await league_service.get_league_by_id(league_id)
            else:
                target_league = await league_service.get_guild_default_league(
                    str(interaction.guild_id) if interaction.guild else ""
                )
                if not target_league:
                    leagues = await league_service.get_user_leagues(str(user.id))
                    if len(leagues) == 1:
                        target_league = leagues[0]

            if not target_league:
                return []

            season = await league_service.get_active_season(str(target_league.id))
            if not season:
                return []

            # Get teams in season
            result = await db.execute(
                select(Team)
                .where(Team.season_id == season.id)
                .where(Team.display_name.ilike(f"%{current}%") if current else True)
                .order_by(Team.display_name)
                .limit(25)
            )
            teams = result.scalars().all()

            return [
                app_commands.Choice(name=team.display_name[:100], value=team.display_name)
                for team in teams
            ]


async def setup(bot: commands.Bot):
    """Set up the team commands cog."""
    await bot.add_cog(TeamCommands(bot))
