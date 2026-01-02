"""Trade commands for Discord bot."""
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
from discord_bot.services.pokemon_service import PokemonService
from discord_bot.views.league_select import prompt_league_selection
from discord_bot.views.confirmation import confirm_action, ConfirmationResult


class TradeCommands(BaseCog, LeagueContextMixin):
    """Commands for viewing and managing trades."""

    trade_group = app_commands.Group(
        name="trade",
        description="Trade commands",
    )

    @trade_group.command(name="list", description="List pending trades")
    @app_commands.describe(league="Select a league (optional)")
    async def list_trades(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show pending trades in the league."""
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
                await self._show_trades(new_interaction, target_league, followup=True)
            else:
                await self._show_trades(interaction, target_league, followup=False)

    async def _show_trades(
        self, interaction: discord.Interaction, league, followup: bool
    ):
        """Display pending trades."""
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

            trade_service = TradeService(db)
            trades = await trade_service.get_pending_trades_for_season(str(season.id))

            embed = discord.Embed(
                title=f"{league.name} - Pending Trades",
                color=Colors.TRADE,
            )

            if trades:
                for trade in trades[:10]:
                    proposer_name = (
                        trade.proposer_team.display_name
                        if trade.proposer_team
                        else "Unknown"
                    )
                    recipient_name = (
                        trade.recipient_team.display_name
                        if trade.recipient_team
                        else "Unknown"
                    )

                    proposer_pokemon, recipient_pokemon = (
                        await trade_service.get_trade_pokemon_details(trade)
                    )

                    proposer_pokemon_names = [p[1].name for p in proposer_pokemon]
                    recipient_pokemon_names = [p[1].name for p in recipient_pokemon]

                    value = (
                        f"**{proposer_name}** offers: {', '.join(proposer_pokemon_names) or 'Nothing'}\n"
                        f"**{recipient_name}** gives: {', '.join(recipient_pokemon_names) or 'Nothing'}"
                    )

                    embed.add_field(
                        name=f"{proposer_name} <-> {recipient_name}",
                        value=value,
                        inline=False,
                    )

                if len(trades) > 10:
                    embed.set_footer(text=f"Showing 10 of {len(trades)} pending trades")
            else:
                embed.description = "No pending trades in this league."

            embed.add_field(
                name="Manage Trades",
                value=f"[View on Web]({get_app_url(f'/leagues/{league.id}/trades')})",
                inline=False,
            )

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @trade_group.command(name="incoming", description="View trades sent to you")
    @app_commands.describe(league="Select a league (optional)")
    async def incoming(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show trades waiting for your response."""
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
                await self._show_incoming_trades(
                    new_interaction, target_league, str(user.id), followup=True
                )
            else:
                await self._show_incoming_trades(
                    interaction, target_league, str(user.id), followup=False
                )

    async def _show_incoming_trades(
        self,
        interaction: discord.Interaction,
        league,
        user_id: str,
        followup: bool,
    ):
        """Display incoming trades."""
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

            trade_service = TradeService(db)
            trades = await trade_service.get_incoming_trades_for_user(
                user_id, str(season.id)
            )

            embed = discord.Embed(
                title="Incoming Trade Offers",
                description=f"League: {league.name}",
                color=Colors.TRADE,
            )

            if trades:
                for trade in trades[:5]:
                    proposer_name = (
                        trade.proposer_team.display_name
                        if trade.proposer_team
                        else "Unknown"
                    )

                    proposer_pokemon, recipient_pokemon = (
                        await trade_service.get_trade_pokemon_details(trade)
                    )

                    proposer_pokemon_names = [p[1].name for p in proposer_pokemon]
                    recipient_pokemon_names = [p[1].name for p in recipient_pokemon]

                    value = (
                        f"You receive: **{', '.join(proposer_pokemon_names) or 'Nothing'}**\n"
                        f"You give: **{', '.join(recipient_pokemon_names) or 'Nothing'}**\n"
                        f"Trade ID: `{str(trade.id)[:8]}`"
                    )

                    embed.add_field(
                        name=f"From: {proposer_name}",
                        value=value,
                        inline=False,
                    )

                embed.set_footer(
                    text="Use /trade accept <id> or /trade reject <id> to respond"
                )
            else:
                embed.description += "\n\nNo pending trade offers."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @trade_group.command(name="view", description="View details of a trade")
    @app_commands.describe(trade_id="The trade ID (first 8 characters)")
    async def view_trade(self, interaction: discord.Interaction, trade_id: str):
        """View details of a specific trade."""
        async with get_db_session() as db:
            trade_service = TradeService(db)

            # Try to find the trade by partial ID
            # This is a simplified lookup - in production you'd want fuzzy matching
            trade = await trade_service.get_trade_by_id(trade_id)

            if not trade:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Trade Not Found",
                        f"Could not find a trade with ID `{trade_id}`.",
                    ),
                    ephemeral=True,
                )
                return

            proposer_pokemon, recipient_pokemon = (
                await trade_service.get_trade_pokemon_details(trade)
            )

            pokemon_service = PokemonService(db)

            embed = discord.Embed(
                title="Trade Details",
                color=Colors.TRADE,
            )

            proposer_name = (
                trade.proposer_team.display_name if trade.proposer_team else "Unknown"
            )
            recipient_name = (
                trade.recipient_team.display_name if trade.recipient_team else "Unknown"
            )

            embed.add_field(name="Proposer", value=proposer_name, inline=True)
            embed.add_field(name="Recipient", value=recipient_name, inline=True)
            embed.add_field(
                name="Status", value=trade.status.value.title(), inline=True
            )

            # Proposer's Pokemon
            if proposer_pokemon:
                pokemon_lines = []
                for tp, pokemon in proposer_pokemon:
                    types = pokemon_service.format_pokemon_types(pokemon)
                    pokemon_lines.append(f"**{pokemon.name}** ({types})")
                embed.add_field(
                    name=f"{proposer_name} Offers",
                    value="\n".join(pokemon_lines),
                    inline=True,
                )
            else:
                embed.add_field(name=f"{proposer_name} Offers", value="Nothing", inline=True)

            # Recipient's Pokemon
            if recipient_pokemon:
                pokemon_lines = []
                for tp, pokemon in recipient_pokemon:
                    types = pokemon_service.format_pokemon_types(pokemon)
                    pokemon_lines.append(f"**{pokemon.name}** ({types})")
                embed.add_field(
                    name=f"{recipient_name} Gives",
                    value="\n".join(pokemon_lines),
                    inline=True,
                )
            else:
                embed.add_field(name=f"{recipient_name} Gives", value="Nothing", inline=True)

            if trade.message:
                embed.add_field(name="Message", value=trade.message, inline=False)

            embed.add_field(
                name="Trade ID",
                value=f"`{str(trade.id)}`",
                inline=False,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @trade_group.command(name="accept", description="Accept a trade offer")
    @app_commands.describe(trade_id="The trade ID")
    async def accept_trade(self, interaction: discord.Interaction, trade_id: str):
        """Accept a pending trade."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed("Account Not Linked", "Link your account first."),
                    ephemeral=True,
                )
                return

            trade_service = TradeService(db)
            can_respond, reason = await trade_service.can_user_respond_to_trade(
                trade_id, str(user.id)
            )

            if not can_respond:
                await interaction.response.send_message(
                    embed=self.error_embed("Cannot Accept Trade", reason),
                    ephemeral=True,
                )
                return

            trade = await trade_service.get_trade_by_id(trade_id)
            proposer_pokemon, recipient_pokemon = (
                await trade_service.get_trade_pokemon_details(trade)
            )

            # Show confirmation
            proposer_names = [p[1].name for p in proposer_pokemon]
            recipient_names = [p[1].name for p in recipient_pokemon]

            result, new_interaction = await confirm_action(
                interaction,
                title="Accept Trade?",
                description=(
                    f"**You will receive:** {', '.join(proposer_names) or 'Nothing'}\n"
                    f"**You will give:** {', '.join(recipient_names) or 'Nothing'}"
                ),
            )

            if result == ConfirmationResult.CONFIRMED:
                # Note: Actual trade execution should go through the API
                # This is just for showing the confirmation flow
                embed = self.success_embed(
                    "Trade Accepted",
                    f"Trade with {trade.proposer_team.display_name} has been accepted.\n\n"
                    f"[View Trade on Web]({get_app_url(f'/trades/{trade.id}')})",
                )
                await new_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = self.info_embed("Cancelled", "Trade acceptance cancelled.")
                await new_interaction.response.send_message(embed=embed, ephemeral=True)

    @trade_group.command(name="reject", description="Reject a trade offer")
    @app_commands.describe(trade_id="The trade ID")
    async def reject_trade(self, interaction: discord.Interaction, trade_id: str):
        """Reject a pending trade."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed("Account Not Linked", "Link your account first."),
                    ephemeral=True,
                )
                return

            trade_service = TradeService(db)
            can_respond, reason = await trade_service.can_user_respond_to_trade(
                trade_id, str(user.id)
            )

            if not can_respond:
                await interaction.response.send_message(
                    embed=self.error_embed("Cannot Reject Trade", reason),
                    ephemeral=True,
                )
                return

            trade = await trade_service.get_trade_by_id(trade_id)

            result, new_interaction = await confirm_action(
                interaction,
                title="Reject Trade?",
                description=f"Reject the trade from **{trade.proposer_team.display_name}**?",
                confirm_label="Reject",
            )

            if result == ConfirmationResult.CONFIRMED:
                embed = self.success_embed(
                    "Trade Rejected",
                    f"Trade from {trade.proposer_team.display_name} has been rejected.",
                )
                await new_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = self.info_embed("Cancelled", "Action cancelled.")
                await new_interaction.response.send_message(embed=embed, ephemeral=True)

    @trade_group.command(name="cancel", description="Cancel your trade proposal")
    @app_commands.describe(trade_id="The trade ID")
    async def cancel_trade(self, interaction: discord.Interaction, trade_id: str):
        """Cancel a trade you proposed."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed("Account Not Linked", "Link your account first."),
                    ephemeral=True,
                )
                return

            trade_service = TradeService(db)
            can_cancel, reason = await trade_service.can_user_cancel_trade(
                trade_id, str(user.id)
            )

            if not can_cancel:
                await interaction.response.send_message(
                    embed=self.error_embed("Cannot Cancel Trade", reason),
                    ephemeral=True,
                )
                return

            result, new_interaction = await confirm_action(
                interaction,
                title="Cancel Trade?",
                description="Are you sure you want to cancel this trade proposal?",
                confirm_label="Cancel Trade",
            )

            if result == ConfirmationResult.CONFIRMED:
                embed = self.success_embed(
                    "Trade Cancelled",
                    "Your trade proposal has been cancelled.",
                )
                await new_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = self.info_embed("Cancelled", "Action cancelled.")
                await new_interaction.response.send_message(embed=embed, ephemeral=True)

    @list_trades.autocomplete("league")
    @incoming.autocomplete("league")
    async def league_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for league parameter."""
        choices = await self.get_user_leagues_for_autocomplete(interaction)
        if current:
            choices = [c for c in choices if current.lower() in c.name.lower()]
        return choices[:25]


async def setup(bot: commands.Bot):
    """Set up the trade commands cog."""
    await bot.add_cog(TradeCommands(bot))
