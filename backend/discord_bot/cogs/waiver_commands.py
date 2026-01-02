"""Waiver commands for Discord bot."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from discord_bot.cogs.base import BaseCog, LeagueContextMixin
from discord_bot.config import Colors, get_app_url
from discord_bot.database import get_db_session
from discord_bot.services.user_service import UserService
from discord_bot.services.league_service import LeagueService
from discord_bot.services.waiver_service import WaiverService
from discord_bot.services.pokemon_service import PokemonService
from discord_bot.views.league_select import prompt_league_selection
from discord_bot.views.confirmation import confirm_action, ConfirmationResult


class WaiverCommands(BaseCog, LeagueContextMixin):
    """Commands for viewing and managing waiver claims."""

    waiver_group = app_commands.Group(
        name="waiver",
        description="Waiver commands",
    )

    @waiver_group.command(name="list", description="List pending waiver claims")
    @app_commands.describe(league="Select a league (optional)")
    async def list_waivers(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show pending waiver claims in the league."""
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
                await self._show_waivers(new_interaction, target_league, followup=True)
            else:
                await self._show_waivers(interaction, target_league, followup=False)

    async def _show_waivers(
        self, interaction: discord.Interaction, league, followup: bool
    ):
        """Display pending waiver claims."""
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

            waiver_service = WaiverService(db)
            waivers = await waiver_service.get_pending_waivers_for_season(
                str(season.id)
            )

            embed = discord.Embed(
                title=f"{league.name} - Pending Waivers",
                color=Colors.WAIVER,
            )

            if waivers:
                pokemon_service = PokemonService(db)

                for waiver in waivers[:10]:
                    team_name = (
                        waiver.team.display_name if waiver.team else "Unknown"
                    )

                    claiming_pokemon, drop_info = (
                        await waiver_service.get_waiver_pokemon_details(waiver)
                    )

                    claim_name = claiming_pokemon.name if claiming_pokemon else "Unknown"
                    drop_name = drop_info[1].name if drop_info else "None"

                    value = f"**Claiming:** {claim_name}\n**Dropping:** {drop_name}"

                    embed.add_field(
                        name=f"{team_name} (#{waiver.priority})",
                        value=value,
                        inline=True,
                    )

                if len(waivers) > 10:
                    embed.set_footer(
                        text=f"Showing 10 of {len(waivers)} pending claims"
                    )
            else:
                embed.description = "No pending waiver claims in this league."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @waiver_group.command(name="my", description="View your waiver claims")
    @app_commands.describe(league="Select a league (optional)")
    async def my_waivers(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show your waiver claims."""
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
                await self._show_my_waivers(
                    new_interaction, target_league, str(user.id), followup=True
                )
            else:
                await self._show_my_waivers(
                    interaction, target_league, str(user.id), followup=False
                )

    async def _show_my_waivers(
        self,
        interaction: discord.Interaction,
        league,
        user_id: str,
        followup: bool,
    ):
        """Display user's waiver claims."""
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

            waiver_service = WaiverService(db)
            waivers = await waiver_service.get_waivers_for_user(user_id, str(season.id))

            embed = discord.Embed(
                title="Your Waiver Claims",
                description=f"League: {league.name}",
                color=Colors.WAIVER,
            )

            if waivers:
                for waiver in waivers[:10]:
                    claiming_pokemon, drop_info = (
                        await waiver_service.get_waiver_pokemon_details(waiver)
                    )

                    claim_name = claiming_pokemon.name if claiming_pokemon else "Unknown"
                    drop_name = drop_info[1].name if drop_info else "None"

                    status_emoji = {
                        "pending": "⏳",
                        "approved": "✅",
                        "rejected": "❌",
                        "cancelled": "🚫",
                        "expired": "⌛",
                    }

                    status = waiver.status.value
                    emoji = status_emoji.get(status, "❓")

                    value = (
                        f"**Claiming:** {claim_name}\n"
                        f"**Dropping:** {drop_name}\n"
                        f"**Status:** {emoji} {status.title()}"
                    )

                    embed.add_field(
                        name=f"Claim #{waiver.priority}",
                        value=value,
                        inline=True,
                    )

                embed.set_footer(
                    text="Use /waiver cancel <id> to cancel pending claims"
                )
            else:
                embed.description += "\n\nYou have no waiver claims."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @waiver_group.command(name="free-agents", description="Browse free agents")
    @app_commands.describe(
        search="Search by Pokemon name",
        league="Select a league (optional)",
    )
    async def free_agents(
        self,
        interaction: discord.Interaction,
        search: Optional[str] = None,
        league: Optional[str] = None,
    ):
        """Browse available free agents."""
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
                await self._show_free_agents(
                    new_interaction, target_league, search, followup=True
                )
            else:
                await self._show_free_agents(
                    interaction, target_league, search, followup=False
                )

    async def _show_free_agents(
        self,
        interaction: discord.Interaction,
        league,
        search: Optional[str],
        followup: bool,
    ):
        """Display available free agents."""
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

            waiver_service = WaiverService(db)
            free_agents = await waiver_service.get_free_agents(
                str(season.id), search=search, limit=20
            )

            title = "Free Agents"
            if search:
                title += f": '{search}'"

            embed = discord.Embed(
                title=title,
                description=f"League: {league.name}",
                color=Colors.WAIVER,
            )

            if free_agents:
                pokemon_service = PokemonService(db)
                lines = []

                for pokemon in free_agents[:15]:
                    types = pokemon_service.format_pokemon_types(pokemon)
                    lines.append(
                        f"**{pokemon.name}** - {types} (BST: {pokemon.base_stat_total})"
                    )

                embed.add_field(
                    name=f"Available ({len(free_agents)}+)",
                    value="\n".join(lines),
                    inline=False,
                )

                if len(free_agents) == 20:
                    embed.set_footer(text="Use search to find specific Pokemon")
            else:
                embed.description += "\n\nNo free agents found."
                if search:
                    embed.description += f" Try a different search."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @waiver_group.command(name="cancel", description="Cancel a waiver claim")
    @app_commands.describe(waiver_id="The waiver claim ID")
    async def cancel_waiver(self, interaction: discord.Interaction, waiver_id: str):
        """Cancel a pending waiver claim."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed("Account Not Linked", "Link your account first."),
                    ephemeral=True,
                )
                return

            waiver_service = WaiverService(db)
            can_cancel, reason = await waiver_service.can_user_cancel_waiver(
                waiver_id, str(user.id)
            )

            if not can_cancel:
                await interaction.response.send_message(
                    embed=self.error_embed("Cannot Cancel Claim", reason),
                    ephemeral=True,
                )
                return

            waiver = await waiver_service.get_waiver_by_id(waiver_id)
            claiming_pokemon, _ = await waiver_service.get_waiver_pokemon_details(waiver)

            pokemon_name = claiming_pokemon.name if claiming_pokemon else "Unknown"

            result, new_interaction = await confirm_action(
                interaction,
                title="Cancel Waiver Claim?",
                description=f"Cancel your claim for **{pokemon_name}**?",
                confirm_label="Cancel Claim",
            )

            if result == ConfirmationResult.CONFIRMED:
                embed = self.success_embed(
                    "Claim Cancelled",
                    f"Your waiver claim for {pokemon_name} has been cancelled.",
                )
                await new_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = self.info_embed("Cancelled", "Action cancelled.")
                await new_interaction.response.send_message(embed=embed, ephemeral=True)

    @list_waivers.autocomplete("league")
    @my_waivers.autocomplete("league")
    @free_agents.autocomplete("league")
    async def league_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for league parameter."""
        choices = await self.get_user_leagues_for_autocomplete(interaction)
        if current:
            choices = [c for c in choices if current.lower() in c.name.lower()]
        return choices[:25]


async def setup(bot: commands.Bot):
    """Set up the waiver commands cog."""
    await bot.add_cog(WaiverCommands(bot))
