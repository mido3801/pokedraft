"""League information commands for Discord bot."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from discord_bot.cogs.base import BaseCog, LeagueContextMixin
from discord_bot.config import Colors, get_app_url
from discord_bot.database import get_db_session
from discord_bot.services.user_service import UserService
from discord_bot.services.league_service import LeagueService
from discord_bot.views.league_select import prompt_league_selection

from app.models import Match
from app.models.season import SeasonStatus
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class LeagueCommands(BaseCog, LeagueContextMixin):
    """Commands for viewing league information."""

    league_group = app_commands.Group(
        name="league",
        description="View league information",
    )

    @league_group.command(name="list", description="List your leagues")
    async def list_leagues(self, interaction: discord.Interaction):
        """Show all leagues the user is a member of."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Account Not Linked",
                        "Link your account with `/account link` to see your leagues.",
                    ),
                    ephemeral=True,
                )
                return

            league_service = LeagueService(db)
            leagues = await league_service.get_user_leagues(str(user.id))

            if not leagues:
                await interaction.response.send_message(
                    embed=self.info_embed(
                        "No Leagues",
                        "You're not a member of any leagues yet.\n"
                        f"Join one at {get_app_url('/leagues')}",
                    ),
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title="Your Leagues",
                color=Colors.INFO,
            )

            for league in leagues[:10]:
                active_season = await league_service.get_active_season(str(league.id))
                season_info = "No active season"
                if active_season:
                    season_info = f"Season {active_season.season_number} - {active_season.status.value}"

                embed.add_field(
                    name=league.name,
                    value=f"Owner: {league.owner.display_name}\n{season_info}",
                    inline=False,
                )

            if len(leagues) > 10:
                embed.set_footer(text=f"And {len(leagues) - 10} more leagues...")

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @league_group.command(name="standings", description="Show league standings")
    @app_commands.describe(league="Select a league (optional)")
    async def standings(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show standings for a league."""
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
                # Need to prompt for selection
                leagues = await league_service.get_user_leagues(str(user.id))
                result = await prompt_league_selection(
                    interaction,
                    leagues,
                    title="Select League for Standings",
                )
                if not result:
                    return
                target_league, interaction = result
                # Followup since we already responded
                await self._show_standings(interaction, target_league, followup=True)
            else:
                await self._show_standings(interaction, target_league, followup=False)

    async def _show_standings(
        self, interaction: discord.Interaction, league, followup: bool
    ):
        """Display standings for a league."""
        async with get_db_session() as db:
            league_service = LeagueService(db)
            season = await league_service.get_active_season(str(league.id))

            if not season:
                embed = self.info_embed(
                    f"{league.name} Standings",
                    "No active season found for this league.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            standings = await league_service.get_standings(str(season.id))

            embed = discord.Embed(
                title=f"{league.name} Standings",
                description=f"Season {season.season_number}",
                color=Colors.INFO,
            )

            if standings:
                standings_text = []
                for i, team in enumerate(standings, 1):
                    record = f"{team.wins}-{team.losses}"
                    if team.ties > 0:
                        record += f"-{team.ties}"
                    user_name = team.user.display_name if team.user else "Unknown"
                    standings_text.append(
                        f"**{i}.** {team.display_name} ({user_name}) - {record}"
                    )

                embed.description += "\n\n" + "\n".join(standings_text)
            else:
                embed.description += "\n\nNo teams found."

            embed.set_footer(text=f"View on web: {get_app_url(f'/leagues/{league.id}')}")

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @league_group.command(name="schedule", description="Show upcoming matches")
    @app_commands.describe(
        league="Select a league (optional)",
        week="Specific week number (optional)",
    )
    async def schedule(
        self,
        interaction: discord.Interaction,
        league: Optional[str] = None,
        week: Optional[int] = None,
    ):
        """Show the schedule for a league."""
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
                    title="Select League for Schedule",
                )
                if not result:
                    return
                target_league, interaction = result
                await self._show_schedule(
                    interaction, target_league, week, followup=True
                )
            else:
                await self._show_schedule(
                    interaction, target_league, week, followup=False
                )

    async def _show_schedule(
        self,
        interaction: discord.Interaction,
        league,
        week: Optional[int],
        followup: bool,
    ):
        """Display schedule for a league."""
        async with get_db_session() as db:
            league_service = LeagueService(db)
            season = await league_service.get_active_season(str(league.id))

            if not season:
                embed = self.info_embed(
                    f"{league.name} Schedule",
                    "No active season found for this league.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Get matches
            query = (
                select(Match)
                .where(Match.season_id == season.id)
                .options(
                    selectinload(Match.team_a).selectinload("user"),
                    selectinload(Match.team_b).selectinload("user"),
                    selectinload(Match.winner),
                )
                .order_by(Match.week, Match.scheduled_at)
            )

            if week is not None:
                query = query.where(Match.week == week)
            else:
                # Show current/upcoming by default
                query = query.where(Match.winner_id.is_(None))
                query = query.where(Match.is_tie == False)

            result = await db.execute(query.limit(15))
            matches = result.scalars().all()

            if week:
                title = f"{league.name} - Week {week}"
            else:
                title = f"{league.name} - Upcoming Matches"

            embed = discord.Embed(
                title=title,
                description=f"Season {season.season_number}",
                color=Colors.MATCH,
            )

            if matches:
                current_week = None
                for match in matches:
                    if match.week != current_week:
                        current_week = match.week
                        if week is None:
                            embed.add_field(
                                name=f"Week {match.week}",
                                value="",
                                inline=False,
                            )

                    team_a_name = match.team_a.display_name if match.team_a else "TBD"
                    team_b_name = match.team_b.display_name if match.team_b else "TBD"

                    if match.winner_id:
                        winner_name = match.winner.display_name if match.winner else ""
                        result_text = f"Winner: {winner_name}"
                    elif match.is_tie:
                        result_text = "Tie"
                    else:
                        result_text = "Pending"

                    time_str = ""
                    if match.scheduled_at:
                        time_str = f"\n<t:{int(match.scheduled_at.timestamp())}:R>"

                    embed.add_field(
                        name=f"{team_a_name} vs {team_b_name}",
                        value=f"{result_text}{time_str}",
                        inline=True,
                    )
            else:
                embed.description += "\n\nNo matches found."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @league_group.command(name="set-default", description="Set the default league for this server")
    @app_commands.describe(league="The league to set as default")
    @app_commands.default_permissions(manage_guild=True)
    async def set_default(self, interaction: discord.Interaction, league: str):
        """Set the default league for the current Discord server."""
        if not interaction.guild:
            await interaction.response.send_message(
                embed=self.error_embed(
                    "Server Only",
                    "This command can only be used in a server.",
                ),
                ephemeral=True,
            )
            return

        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Account Not Linked",
                        "Link your account first.",
                    ),
                    ephemeral=True,
                )
                return

            league_service = LeagueService(db)
            target_league = await league_service.get_league_by_id(league)

            if not target_league:
                await interaction.response.send_message(
                    embed=self.error_embed("League Not Found", "Invalid league ID."),
                    ephemeral=True,
                )
                return

            # Check if user is member
            is_member = await league_service.is_league_member(
                str(user.id), str(target_league.id)
            )
            if not is_member:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Not a Member",
                        "You must be a member of a league to set it as default.",
                    ),
                    ephemeral=True,
                )
                return

            # Set the default
            await league_service.set_guild_league(
                str(interaction.guild.id),
                str(target_league.id),
            )

            await interaction.response.send_message(
                embed=self.success_embed(
                    "Default League Set",
                    f"**{target_league.name}** is now the default league for this server.\n\n"
                    "League commands will use this league by default.",
                ),
                ephemeral=True,
            )

    @standings.autocomplete("league")
    @schedule.autocomplete("league")
    @set_default.autocomplete("league")
    async def league_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for league parameter."""
        choices = await self.get_user_leagues_for_autocomplete(interaction)
        if current:
            choices = [c for c in choices if current.lower() in c.name.lower()]
        return choices[:25]


async def setup(bot: commands.Bot):
    """Set up the league commands cog."""
    await bot.add_cog(LeagueCommands(bot))
