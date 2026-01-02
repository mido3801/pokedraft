"""Draft commands for Discord bot."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from discord_bot.cogs.base import BaseCog, LeagueContextMixin
from discord_bot.config import Colors, get_app_url, get_pokemon_sprite, Pagination
from discord_bot.database import get_db_session
from discord_bot.services.user_service import UserService
from discord_bot.services.league_service import LeagueService
from discord_bot.services.draft_service import DraftService
from discord_bot.services.pokemon_service import PokemonService
from discord_bot.views.league_select import prompt_league_selection


class DraftCommands(BaseCog, LeagueContextMixin):
    """Commands for viewing and participating in drafts."""

    draft_group = app_commands.Group(
        name="draft",
        description="Draft commands",
    )

    @draft_group.command(name="info", description="Get info about the current draft")
    @app_commands.describe(league="Select a league (optional)")
    async def info(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show information about the current draft."""
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
                    title="Select League for Draft",
                )
                if not result:
                    return
                target_league, new_interaction = result
                await self._show_draft_info(new_interaction, target_league, followup=True)
            else:
                await self._show_draft_info(interaction, target_league, followup=False)

    async def _show_draft_info(
        self, interaction: discord.Interaction, league, followup: bool
    ):
        """Display draft information."""
        async with get_db_session() as db:
            draft_service = DraftService(db)
            draft = await draft_service.get_draft_for_league(str(league.id))

            if not draft:
                embed = self.info_embed(
                    f"{league.name} Draft",
                    "No active draft found for this league.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            status_info = await draft_service.get_draft_status_info(str(draft.id))

            embed = discord.Embed(
                title=f"{league.name} Draft",
                color=Colors.DRAFT,
            )

            # Status
            status_emoji = {
                "live": "🟢",
                "paused": "⏸️",
                "pending": "⏳",
                "completed": "✅",
            }
            status = status_info["status"]
            embed.add_field(
                name="Status",
                value=f"{status_emoji.get(status, '❓')} {status.title()}",
                inline=True,
            )

            embed.add_field(
                name="Format",
                value=status_info["format"].title(),
                inline=True,
            )

            embed.add_field(
                name="Teams",
                value=str(status_info["team_count"]),
                inline=True,
            )

            # Progress
            picks_made = status_info["picks_made"]
            total_picks = status_info["total_picks"]
            if total_picks > 0:
                progress_pct = (picks_made / total_picks) * 100
                embed.add_field(
                    name="Progress",
                    value=f"{picks_made}/{total_picks} picks ({progress_pct:.0f}%)",
                    inline=True,
                )

            embed.add_field(
                name="Roster Size",
                value=str(status_info["roster_size"]),
                inline=True,
            )

            if status_info["timer_seconds"]:
                embed.add_field(
                    name="Timer",
                    value=f"{status_info['timer_seconds']}s",
                    inline=True,
                )

            # Current picker
            current_picker = status_info["current_picker"]
            if current_picker and status == "live":
                picker_name = (
                    current_picker.user.display_name
                    if current_picker.user
                    else current_picker.display_name
                )
                embed.add_field(
                    name="🎯 On the Clock",
                    value=f"**{current_picker.display_name}** ({picker_name})",
                    inline=False,
                )

            # Recent picks
            recent_picks = status_info["recent_picks"]
            if recent_picks:
                picks_text = []
                for pick, team, pokemon in recent_picks[:5]:
                    picks_text.append(
                        f"**#{pick.pick_number}** {team.display_name}: {pokemon.name}"
                    )
                embed.add_field(
                    name="Recent Picks",
                    value="\n".join(picks_text),
                    inline=False,
                )

            # Link to draft room
            embed.add_field(
                name="Draft Room",
                value=f"[Join Draft]({get_app_url(f'/draft/{draft.id}')})",
                inline=False,
            )

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @draft_group.command(name="picks", description="Show recent picks")
    @app_commands.describe(
        count="Number of picks to show (default 10)",
        league="Select a league (optional)",
    )
    async def picks(
        self,
        interaction: discord.Interaction,
        count: int = 10,
        league: Optional[str] = None,
    ):
        """Show recent picks in the draft."""
        count = min(max(count, 1), Pagination.PICKS_PAGE_SIZE * 2)

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
                await self._show_picks(new_interaction, target_league, count, followup=True)
            else:
                await self._show_picks(interaction, target_league, count, followup=False)

    async def _show_picks(
        self, interaction: discord.Interaction, league, count: int, followup: bool
    ):
        """Display recent picks."""
        async with get_db_session() as db:
            draft_service = DraftService(db)
            draft = await draft_service.get_draft_for_league(str(league.id))

            if not draft:
                embed = self.info_embed(
                    "No Active Draft",
                    "There's no active draft in this league.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            picks = await draft_service.get_recent_picks(str(draft.id), limit=count)

            embed = discord.Embed(
                title=f"{league.name} - Recent Picks",
                color=Colors.DRAFT,
            )

            if picks:
                pokemon_service = PokemonService(db)
                picks_text = []

                for pick, team, pokemon in picks:
                    types = pokemon_service.format_pokemon_types(pokemon)
                    picks_text.append(
                        f"**#{pick.pick_number}** {team.display_name}: "
                        f"**{pokemon.name}** ({types})"
                    )

                embed.description = "\n".join(picks_text)

                # Set thumbnail to most recent pick
                if picks:
                    embed.set_thumbnail(url=get_pokemon_sprite(picks[0][2].id))
            else:
                embed.description = "No picks have been made yet."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @draft_group.command(name="available", description="Search available Pokemon")
    @app_commands.describe(
        query="Search query",
        league="Select a league (optional)",
    )
    async def available(
        self,
        interaction: discord.Interaction,
        query: str,
        league: Optional[str] = None,
    ):
        """Search for available Pokemon in the draft."""
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
                await self._show_available(
                    new_interaction, target_league, query, followup=True
                )
            else:
                await self._show_available(
                    interaction, target_league, query, followup=False
                )

    async def _show_available(
        self, interaction: discord.Interaction, league, query: str, followup: bool
    ):
        """Display available Pokemon."""
        async with get_db_session() as db:
            draft_service = DraftService(db)
            draft = await draft_service.get_draft_for_league(str(league.id))

            if not draft:
                embed = self.info_embed(
                    "No Active Draft",
                    "There's no active draft in this league.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            available = await draft_service.get_available_pokemon(
                str(draft.id), search=query, limit=15
            )

            embed = discord.Embed(
                title=f"Available Pokemon: '{query}'",
                color=Colors.DRAFT,
            )

            if available:
                pokemon_service = PokemonService(db)
                result_lines = []

                for pokemon in available:
                    types = pokemon_service.format_pokemon_types(pokemon)
                    result_lines.append(
                        f"**{pokemon.name}** - {types} (BST: {pokemon.base_stat_total})"
                    )

                embed.description = "\n".join(result_lines)

                if len(available) == 15:
                    embed.set_footer(text="Showing first 15 results")
            else:
                embed.description = f"No available Pokemon matching '{query}'."

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @draft_group.command(name="mypicks", description="View your draft picks")
    @app_commands.describe(league="Select a league (optional)")
    async def mypicks(
        self, interaction: discord.Interaction, league: Optional[str] = None
    ):
        """Show the user's picks in the current draft."""
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
                await self._show_my_picks(
                    new_interaction, target_league, str(user.id), followup=True
                )
            else:
                await self._show_my_picks(
                    interaction, target_league, str(user.id), followup=False
                )

    async def _show_my_picks(
        self,
        interaction: discord.Interaction,
        league,
        user_id: str,
        followup: bool,
    ):
        """Display user's draft picks."""
        async with get_db_session() as db:
            draft_service = DraftService(db)
            draft = await draft_service.get_draft_for_league(str(league.id))

            if not draft:
                embed = self.info_embed(
                    "No Active Draft",
                    "There's no active draft in this league.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            team = await draft_service.get_user_team_in_draft(str(draft.id), user_id)
            if not team:
                embed = self.error_embed(
                    "Not in Draft",
                    "You don't have a team in this draft.",
                )
                if followup:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            picks = await draft_service.get_picks_by_team(str(draft.id), str(team.id))

            embed = discord.Embed(
                title=f"{team.display_name}'s Picks",
                description=f"Draft: {league.name}",
                color=Colors.DRAFT,
            )

            if picks:
                pokemon_service = PokemonService(db)
                picks_text = []

                for pick, pokemon in picks:
                    types = pokemon_service.format_pokemon_types(pokemon)
                    picks_text.append(
                        f"**#{pick.pick_number}** {pokemon.name} ({types})"
                    )

                embed.add_field(
                    name=f"Picks ({len(picks)}/{draft.roster_size})",
                    value="\n".join(picks_text),
                    inline=False,
                )

                # Set thumbnail to first pick
                embed.set_thumbnail(url=get_pokemon_sprite(picks[0][1].id))
            else:
                embed.add_field(
                    name="Picks",
                    value="No picks yet",
                    inline=False,
                )

            if followup:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @info.autocomplete("league")
    @picks.autocomplete("league")
    @available.autocomplete("league")
    @mypicks.autocomplete("league")
    async def league_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for league parameter."""
        choices = await self.get_user_leagues_for_autocomplete(interaction)
        if current:
            choices = [c for c in choices if current.lower() in c.name.lower()]
        return choices[:25]


async def setup(bot: commands.Bot):
    """Set up the draft commands cog."""
    await bot.add_cog(DraftCommands(bot))
