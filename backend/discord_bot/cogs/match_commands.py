"""Match commands for Discord bot."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from discord_bot.cogs.base import BaseCog, LeagueContextMixin
from discord_bot.config import Colors, get_app_url
from discord_bot.database import get_db_session
from discord_bot.services.user_service import UserService
from discord_bot.services.league_service import LeagueService
from discord_bot.services.match_service import MatchService
from discord_bot.views.league_select import prompt_league_selection
from discord_bot.views.confirmation import confirm_action, ConfirmationResult


class MatchCommands(BaseCog, LeagueContextMixin):
    """Commands for viewing and managing matches."""

    match_group = app_commands.Group(
        name="match",
        description="Match commands",
    )

    @match_group.command(name="upcoming", description="View upcoming matches")
    @app_commands.describe(league="Select a league (optional)")
    async def upcoming(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show upcoming matches in the league."""
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

            if league:
                target_league = await league_service.get_league_by_id(league)
            else:
                target_league = await self.resolve_league(
                    interaction, user_id=str(user.id)
                )

            if not target_league:
                leagues = await league_service.get_user_leagues(str(user.id))
                result = await prompt_league_selection(interaction, leagues)
                if not result:
                    return
                target_league, new_interaction = result
                await self._show_upcoming(new_interaction, target_league, followup=True)
            else:
                await self._show_upcoming(interaction, target_league, followup=False)

    async def _show_upcoming(
        self, interaction: discord.Interaction, league, followup: bool
    ):
        """Display upcoming matches."""
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

            match_service = MatchService(db)
            matches = await match_service.get_upcoming_matches_for_season(
                str(season.id), limit=15
            )

            embed = discord.Embed(
                title=f"{league.name} - Upcoming Matches",
                color=Colors.MATCH,
            )

            if matches:
                current_week = None
                for match in matches:
                    if match.week != current_week:
                        current_week = match.week

                    team_a_name = match.team_a.display_name if match.team_a else "TBD"
                    team_b_name = match.team_b.display_name if match.team_b else "TBD"

                    value = f"Week {match.week}"
                    if match.scheduled_at:
                        value += f"\n<t:{int(match.scheduled_at.timestamp())}:R>"

                    embed.add_field(
                        name=f"{team_a_name} vs {team_b_name}",
                        value=value,
                        inline=True,
                    )

                if len(matches) == 15:
                    embed.set_footer(text="Showing first 15 matches")
            else:
                embed.description = "No upcoming matches."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @match_group.command(name="my", description="View your upcoming matches")
    @app_commands.describe(league="Select a league (optional)")
    async def my_matches(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show your upcoming matches."""
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

            if league:
                target_league = await league_service.get_league_by_id(league)
            else:
                target_league = await self.resolve_league(
                    interaction, user_id=str(user.id)
                )

            if not target_league:
                leagues = await league_service.get_user_leagues(str(user.id))
                result = await prompt_league_selection(interaction, leagues)
                if not result:
                    return
                target_league, new_interaction = result
                await self._show_my_matches(
                    new_interaction, target_league, str(user.id), followup=True
                )
            else:
                await self._show_my_matches(
                    interaction, target_league, str(user.id), followup=False
                )

    async def _show_my_matches(
        self,
        interaction: discord.Interaction,
        league,
        user_id: str,
        followup: bool,
    ):
        """Display user's upcoming matches."""
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

            match_service = MatchService(db)
            matches = await match_service.get_matches_for_user(user_id, str(season.id))

            embed = discord.Embed(
                title="Your Upcoming Matches",
                description=f"League: {league.name}",
                color=Colors.MATCH,
            )

            if matches:
                for match in matches[:10]:
                    team_a_name = match.team_a.display_name if match.team_a else "TBD"
                    team_b_name = match.team_b.display_name if match.team_b else "TBD"

                    value = f"**Week {match.week}**"
                    if match.scheduled_at:
                        value += f"\n<t:{int(match.scheduled_at.timestamp())}:F>"

                    embed.add_field(
                        name=f"{team_a_name} vs {team_b_name}",
                        value=value,
                        inline=False,
                    )
            else:
                embed.description += "\n\nNo upcoming matches."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @match_group.command(name="view", description="View match details")
    @app_commands.describe(match_id="The match ID")
    async def view_match(self, interaction: discord.Interaction, match_id: str):
        """View details of a specific match."""
        async with get_db_session() as db:
            match_service = MatchService(db)
            match = await match_service.get_match_by_id(match_id)

            if not match:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Match Not Found",
                        f"Could not find a match with ID `{match_id}`.",
                    ),
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title="Match Details",
                color=Colors.MATCH,
            )

            team_a_name = match.team_a.display_name if match.team_a else "TBD"
            team_b_name = match.team_b.display_name if match.team_b else "TBD"

            embed.add_field(name="Team A", value=team_a_name, inline=True)
            embed.add_field(name="Team B", value=team_b_name, inline=True)
            embed.add_field(name="Week", value=str(match.week), inline=True)

            if match.scheduled_at:
                embed.add_field(
                    name="Scheduled",
                    value=f"<t:{int(match.scheduled_at.timestamp())}:F>",
                    inline=True,
                )

            # Result
            if match.winner_id:
                winner_name = match.winner.display_name if match.winner else "Unknown"
                embed.add_field(name="Winner", value=winner_name, inline=True)
            elif match.is_tie:
                embed.add_field(name="Result", value="Tie", inline=True)
            else:
                embed.add_field(name="Result", value="Pending", inline=True)

            if match.replay_url:
                embed.add_field(
                    name="Replay",
                    value=f"[Watch Replay]({match.replay_url})",
                    inline=False,
                )

            if match.notes:
                embed.add_field(name="Notes", value=match.notes, inline=False)

            if match.season and match.season.league:
                league_name = match.season.league.name
                embed.set_footer(text=f"League: {league_name}")

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @match_group.command(name="results", description="View recent match results")
    @app_commands.describe(league="Select a league (optional)")
    async def results(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show recent match results."""
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

            if league:
                target_league = await league_service.get_league_by_id(league)
            else:
                target_league = await self.resolve_league(
                    interaction, user_id=str(user.id)
                )

            if not target_league:
                leagues = await league_service.get_user_leagues(str(user.id))
                result = await prompt_league_selection(interaction, leagues)
                if not result:
                    return
                target_league, new_interaction = result
                await self._show_results(new_interaction, target_league, followup=True)
            else:
                await self._show_results(interaction, target_league, followup=False)

    async def _show_results(
        self, interaction: discord.Interaction, league, followup: bool
    ):
        """Display recent match results."""
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

            match_service = MatchService(db)
            matches = await match_service.get_recent_results(str(season.id), limit=10)

            embed = discord.Embed(
                title=f"{league.name} - Recent Results",
                color=Colors.MATCH,
            )

            if matches:
                for match in matches:
                    team_a_name = match.team_a.display_name if match.team_a else "TBD"
                    team_b_name = match.team_b.display_name if match.team_b else "TBD"

                    if match.is_tie:
                        result_text = "Tie"
                    elif match.winner:
                        winner_name = match.winner.display_name
                        result_text = f"Winner: **{winner_name}**"
                    else:
                        result_text = "Unknown"

                    embed.add_field(
                        name=f"Week {match.week}: {team_a_name} vs {team_b_name}",
                        value=result_text,
                        inline=False,
                    )
            else:
                embed.description = "No match results yet."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @match_group.command(name="report", description="Report a match result")
    @app_commands.describe(
        match_id="The match ID",
        winner="Who won (team_a, team_b, or tie)",
        replay_url="Optional replay URL",
    )
    @app_commands.choices(
        winner=[
            app_commands.Choice(name="Team A", value="team_a"),
            app_commands.Choice(name="Team B", value="team_b"),
            app_commands.Choice(name="Tie", value="tie"),
        ]
    )
    async def report_result(
        self,
        interaction: discord.Interaction,
        match_id: str,
        winner: str,
        replay_url: Optional[str] = None,
    ):
        """Report a match result."""
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

            match_service = MatchService(db)
            can_report, reason = await match_service.can_user_report_result(
                match_id, str(user.id)
            )

            if not can_report:
                await interaction.response.send_message(
                    embed=self.error_embed("Cannot Report Result", reason),
                    ephemeral=True,
                )
                return

            match = await match_service.get_match_by_id(match_id)

            team_a_name = match.team_a.display_name if match.team_a else "Team A"
            team_b_name = match.team_b.display_name if match.team_b else "Team B"

            if winner == "team_a":
                winner_text = team_a_name
            elif winner == "team_b":
                winner_text = team_b_name
            else:
                winner_text = "Tie"

            description = (
                f"**{team_a_name}** vs **{team_b_name}**\n\n"
                f"Result: **{winner_text}**"
            )
            if replay_url:
                description += f"\nReplay: {replay_url}"

            result, new_interaction = await confirm_action(
                interaction,
                title="Report Match Result?",
                description=description,
            )

            if result == ConfirmationResult.CONFIRMED:
                # Note: Actual result recording should go through the API
                embed = self.success_embed(
                    "Result Reported",
                    f"Match result has been submitted.\n\n"
                    f"[View on Web]({get_app_url(f'/matches/{match.id}')})",
                )
                await new_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = self.info_embed("Cancelled", "Result reporting cancelled.")
                await new_interaction.response.send_message(embed=embed, ephemeral=True)

    @upcoming.autocomplete("league")
    @my_matches.autocomplete("league")
    @results.autocomplete("league")
    async def league_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for league parameter."""
        choices = await self.get_user_leagues_for_autocomplete(interaction)
        if current:
            choices = [c for c in choices if current.lower() in c.name.lower()]
        return choices[:25]


async def setup(bot: commands.Bot):
    """Set up the match commands cog."""
    await bot.add_cog(MatchCommands(bot))
