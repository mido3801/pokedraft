"""Admin commands for Discord bot."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from discord_bot.cogs.base import BaseCog, LeagueContextMixin
from discord_bot.config import Colors, get_app_url
from discord_bot.database import get_db_session
from discord_bot.services.user_service import UserService
from discord_bot.services.league_service import LeagueService
from discord_bot.services.trade_service import TradeService
from discord_bot.services.waiver_service import WaiverService
from discord_bot.views.league_select import prompt_league_selection
from discord_bot.views.confirmation import confirm_action, ConfirmationResult


class AdminCommands(BaseCog, LeagueContextMixin):
    """Admin commands for league management."""

    admin_group = app_commands.Group(
        name="admin",
        description="Admin commands (league owners only)",
    )

    async def _check_admin(
        self, interaction: discord.Interaction, league_id: str
    ) -> tuple[bool, Optional[str]]:
        """Check if the user is a league admin.

        Returns:
            Tuple of (is_admin, user_id).
        """
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
                return (False, None)

            league_service = LeagueService(db)
            is_owner = await league_service.is_league_owner(str(user.id), league_id)

            if not is_owner:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Permission Denied",
                        "Only league owners can use admin commands.",
                    ),
                    ephemeral=True,
                )
                return (False, None)

            return (True, str(user.id))

    @admin_group.command(name="pending", description="View items awaiting approval")
    @app_commands.describe(league="Select a league (optional)")
    async def pending(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show trades and waivers awaiting admin approval."""
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
                await self._show_pending(
                    new_interaction, target_league, str(user.id), followup=True
                )
            else:
                await self._show_pending(
                    interaction, target_league, str(user.id), followup=False
                )

    async def _show_pending(
        self,
        interaction: discord.Interaction,
        league,
        user_id: str,
        followup: bool,
    ):
        """Display pending items for admin approval."""
        async with get_db_session() as db:
            league_service = LeagueService(db)

            # Check if user is owner
            is_owner = await league_service.is_league_owner(user_id, str(league.id))
            if not is_owner:
                embed = self.error_embed(
                    "Permission Denied",
                    "Only league owners can view pending approvals.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

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

            trade_service = TradeService(db)
            waiver_service = WaiverService(db)

            pending_trades = await trade_service.get_trades_awaiting_admin_approval(
                str(season.id)
            )
            pending_waivers = await waiver_service.get_waivers_awaiting_admin_approval(
                str(season.id)
            )

            embed = discord.Embed(
                title=f"{league.name} - Pending Approvals",
                color=Colors.WARNING,
            )

            # Pending trades
            if pending_trades:
                trade_lines = []
                for trade in pending_trades[:5]:
                    proposer = (
                        trade.proposer_team.display_name
                        if trade.proposer_team
                        else "?"
                    )
                    recipient = (
                        trade.recipient_team.display_name
                        if trade.recipient_team
                        else "?"
                    )
                    trade_lines.append(
                        f"**{proposer}** <-> **{recipient}**\nID: `{str(trade.id)[:8]}`"
                    )
                embed.add_field(
                    name=f"Trades ({len(pending_trades)})",
                    value="\n\n".join(trade_lines),
                    inline=False,
                )
            else:
                embed.add_field(name="Trades", value="None pending", inline=False)

            # Pending waivers
            if pending_waivers:
                waiver_lines = []
                for waiver in pending_waivers[:5]:
                    team_name = (
                        waiver.team.display_name if waiver.team else "?"
                    )
                    claiming, _ = await waiver_service.get_waiver_pokemon_details(waiver)
                    pokemon_name = claiming.name if claiming else "?"
                    waiver_lines.append(
                        f"**{team_name}** claiming **{pokemon_name}**\nID: `{str(waiver.id)[:8]}`"
                    )
                embed.add_field(
                    name=f"Waivers ({len(pending_waivers)})",
                    value="\n\n".join(waiver_lines),
                    inline=False,
                )
            else:
                embed.add_field(name="Waivers", value="None pending", inline=False)

            embed.set_footer(
                text="Use /admin trade approve/reject or /admin waiver approve/reject"
            )

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    # Trade approval subgroup
    trade_admin = app_commands.Group(
        name="trade",
        description="Trade admin commands",
        parent=admin_group,
    )

    @trade_admin.command(name="approve", description="Approve a trade")
    @app_commands.describe(trade_id="The trade ID")
    async def approve_trade(self, interaction: discord.Interaction, trade_id: str):
        """Approve a pending trade."""
        async with get_db_session() as db:
            trade_service = TradeService(db)
            trade = await trade_service.get_trade_by_id(trade_id)

            if not trade:
                await interaction.response.send_message(
                    embed=self.error_embed("Trade Not Found", "Invalid trade ID."),
                    ephemeral=True,
                )
                return

            if not trade.season or not trade.season.league:
                await interaction.response.send_message(
                    embed=self.error_embed("Error", "Could not determine league."),
                    ephemeral=True,
                )
                return

            is_admin, user_id = await self._check_admin(
                interaction, str(trade.season.league.id)
            )
            if not is_admin:
                return

            proposer_pokemon, recipient_pokemon = (
                await trade_service.get_trade_pokemon_details(trade)
            )

            proposer_names = [p[1].name for p in proposer_pokemon]
            recipient_names = [p[1].name for p in recipient_pokemon]

            result, new_interaction = await confirm_action(
                interaction,
                title="Approve Trade?",
                description=(
                    f"**{trade.proposer_team.display_name}** gives: "
                    f"{', '.join(proposer_names) or 'Nothing'}\n"
                    f"**{trade.recipient_team.display_name}** gives: "
                    f"{', '.join(recipient_names) or 'Nothing'}"
                ),
                confirm_label="Approve",
            )

            if result == ConfirmationResult.CONFIRMED:
                embed = self.success_embed(
                    "Trade Approved",
                    "The trade has been approved and will be processed.",
                )
                await new_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = self.info_embed("Cancelled", "Action cancelled.")
                await new_interaction.response.send_message(embed=embed, ephemeral=True)

    @trade_admin.command(name="reject", description="Reject a trade")
    @app_commands.describe(
        trade_id="The trade ID",
        reason="Reason for rejection",
    )
    async def reject_trade(
        self,
        interaction: discord.Interaction,
        trade_id: str,
        reason: Optional[str] = None,
    ):
        """Reject a pending trade."""
        async with get_db_session() as db:
            trade_service = TradeService(db)
            trade = await trade_service.get_trade_by_id(trade_id)

            if not trade:
                await interaction.response.send_message(
                    embed=self.error_embed("Trade Not Found", "Invalid trade ID."),
                    ephemeral=True,
                )
                return

            if not trade.season or not trade.season.league:
                await interaction.response.send_message(
                    embed=self.error_embed("Error", "Could not determine league."),
                    ephemeral=True,
                )
                return

            is_admin, user_id = await self._check_admin(
                interaction, str(trade.season.league.id)
            )
            if not is_admin:
                return

            description = (
                f"Reject trade between **{trade.proposer_team.display_name}** "
                f"and **{trade.recipient_team.display_name}**?"
            )
            if reason:
                description += f"\n\nReason: {reason}"

            result, new_interaction = await confirm_action(
                interaction,
                title="Reject Trade?",
                description=description,
                confirm_label="Reject",
            )

            if result == ConfirmationResult.CONFIRMED:
                embed = self.success_embed(
                    "Trade Rejected",
                    "The trade has been rejected.",
                )
                await new_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = self.info_embed("Cancelled", "Action cancelled.")
                await new_interaction.response.send_message(embed=embed, ephemeral=True)

    # Waiver approval subgroup
    waiver_admin = app_commands.Group(
        name="waiver",
        description="Waiver admin commands",
        parent=admin_group,
    )

    @waiver_admin.command(name="approve", description="Approve a waiver claim")
    @app_commands.describe(waiver_id="The waiver claim ID")
    async def approve_waiver(self, interaction: discord.Interaction, waiver_id: str):
        """Approve a pending waiver claim."""
        async with get_db_session() as db:
            waiver_service = WaiverService(db)
            waiver = await waiver_service.get_waiver_by_id(waiver_id)

            if not waiver:
                await interaction.response.send_message(
                    embed=self.error_embed("Waiver Not Found", "Invalid waiver ID."),
                    ephemeral=True,
                )
                return

            if not waiver.season or not waiver.season.league:
                await interaction.response.send_message(
                    embed=self.error_embed("Error", "Could not determine league."),
                    ephemeral=True,
                )
                return

            is_admin, user_id = await self._check_admin(
                interaction, str(waiver.season.league.id)
            )
            if not is_admin:
                return

            claiming, drop_info = await waiver_service.get_waiver_pokemon_details(waiver)
            team_name = waiver.team.display_name if waiver.team else "Unknown"
            pokemon_name = claiming.name if claiming else "Unknown"
            drop_name = drop_info[1].name if drop_info else "None"

            result, new_interaction = await confirm_action(
                interaction,
                title="Approve Waiver Claim?",
                description=(
                    f"**{team_name}** claiming **{pokemon_name}**\n"
                    f"Dropping: {drop_name}"
                ),
                confirm_label="Approve",
            )

            if result == ConfirmationResult.CONFIRMED:
                embed = self.success_embed(
                    "Waiver Approved",
                    "The waiver claim has been approved.",
                )
                await new_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = self.info_embed("Cancelled", "Action cancelled.")
                await new_interaction.response.send_message(embed=embed, ephemeral=True)

    @waiver_admin.command(name="reject", description="Reject a waiver claim")
    @app_commands.describe(
        waiver_id="The waiver claim ID",
        reason="Reason for rejection",
    )
    async def reject_waiver(
        self,
        interaction: discord.Interaction,
        waiver_id: str,
        reason: Optional[str] = None,
    ):
        """Reject a pending waiver claim."""
        async with get_db_session() as db:
            waiver_service = WaiverService(db)
            waiver = await waiver_service.get_waiver_by_id(waiver_id)

            if not waiver:
                await interaction.response.send_message(
                    embed=self.error_embed("Waiver Not Found", "Invalid waiver ID."),
                    ephemeral=True,
                )
                return

            if not waiver.season or not waiver.season.league:
                await interaction.response.send_message(
                    embed=self.error_embed("Error", "Could not determine league."),
                    ephemeral=True,
                )
                return

            is_admin, user_id = await self._check_admin(
                interaction, str(waiver.season.league.id)
            )
            if not is_admin:
                return

            claiming, _ = await waiver_service.get_waiver_pokemon_details(waiver)
            team_name = waiver.team.display_name if waiver.team else "Unknown"
            pokemon_name = claiming.name if claiming else "Unknown"

            description = f"Reject **{team_name}**'s claim for **{pokemon_name}**?"
            if reason:
                description += f"\n\nReason: {reason}"

            result, new_interaction = await confirm_action(
                interaction,
                title="Reject Waiver Claim?",
                description=description,
                confirm_label="Reject",
            )

            if result == ConfirmationResult.CONFIRMED:
                embed = self.success_embed(
                    "Waiver Rejected",
                    "The waiver claim has been rejected.",
                )
                await new_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = self.info_embed("Cancelled", "Action cancelled.")
                await new_interaction.response.send_message(embed=embed, ephemeral=True)

    @pending.autocomplete("league")
    async def league_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for league parameter."""
        choices = await self.get_user_leagues_for_autocomplete(interaction)
        if current:
            choices = [c for c in choices if current.lower() in c.name.lower()]
        return choices[:25]


async def setup(bot: commands.Bot):
    """Set up the admin commands cog."""
    await bot.add_cog(AdminCommands(bot))
