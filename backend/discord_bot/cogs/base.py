"""Base cog utilities and mixins for Discord bot commands."""
import logging
from typing import Optional, TypeVar, Generic
from functools import wraps

import discord
from discord.ext import commands
from discord import app_commands

from discord_bot.config import Colors
from discord_bot.database import get_db_session
from discord_bot.services.user_service import UserService
from discord_bot.services.league_service import LeagueService

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseCog(commands.Cog):
    """Base class for all bot cogs with common utilities."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_linked_user(
        self, interaction: discord.Interaction
    ) -> Optional["User"]:
        """Get the linked PokeDraft user for a Discord user.

        Returns None if the user hasn't linked their account.
        """
        async with get_db_session() as db:
            user_service = UserService(db)
            return await user_service.get_user_by_discord_id(str(interaction.user.id))

    async def require_linked_user(
        self, interaction: discord.Interaction
    ) -> Optional["User"]:
        """Get the linked user or send an error message.

        Returns the user if linked, or None after sending an error response.
        """
        user = await self.get_linked_user(interaction)
        if not user:
            await interaction.response.send_message(
                embed=self.error_embed(
                    "Account Not Linked",
                    "You need to link your Discord account first.\n"
                    "Use `/account link` to get started.",
                ),
                ephemeral=True,
            )
            return None
        return user

    def success_embed(
        self,
        title: str,
        description: str = "",
        **kwargs,
    ) -> discord.Embed:
        """Create a success embed."""
        return discord.Embed(
            title=title,
            description=description,
            color=Colors.SUCCESS,
            **kwargs,
        )

    def error_embed(
        self,
        title: str,
        description: str = "",
        **kwargs,
    ) -> discord.Embed:
        """Create an error embed."""
        return discord.Embed(
            title=title,
            description=description,
            color=Colors.ERROR,
            **kwargs,
        )

    def info_embed(
        self,
        title: str,
        description: str = "",
        **kwargs,
    ) -> discord.Embed:
        """Create an info embed."""
        return discord.Embed(
            title=title,
            description=description,
            color=Colors.INFO,
            **kwargs,
        )

    def warning_embed(
        self,
        title: str,
        description: str = "",
        **kwargs,
    ) -> discord.Embed:
        """Create a warning embed."""
        return discord.Embed(
            title=title,
            description=description,
            color=Colors.WARNING,
            **kwargs,
        )

    async def handle_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        context: str = "command",
    ) -> None:
        """Handle an error and send an appropriate response."""
        logger.exception(f"Error in {context}: {error}")

        error_message = str(error)
        if len(error_message) > 200:
            error_message = error_message[:200] + "..."

        embed = self.error_embed(
            "Something went wrong",
            f"An error occurred while processing your request.\n\n```{error_message}```",
        )

        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.errors.HTTPException:
            logger.error("Failed to send error message to user")


class LeagueContextMixin:
    """Mixin for cogs that need league context resolution."""

    async def resolve_league(
        self,
        interaction: discord.Interaction,
        league_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional["League"]:
        """Resolve which league to use based on context.

        Priority:
        1. Explicit league_id parameter
        2. Server default from discord_guild_configs
        3. User's only league (if they have exactly one)
        4. None (caller should prompt for selection)
        """
        async with get_db_session() as db:
            league_service = LeagueService(db)

            # 1. Explicit league_id
            if league_id:
                return await league_service.get_league_by_id(league_id)

            # 2. Server default
            guild_id = str(interaction.guild_id) if interaction.guild else None
            if guild_id:
                default_league = await league_service.get_guild_default_league(guild_id)
                if default_league:
                    return default_league

            # 3. User's only league
            if user_id:
                user_leagues = await league_service.get_user_leagues(user_id)
                if len(user_leagues) == 1:
                    return user_leagues[0]

            return None

    async def get_user_leagues_for_autocomplete(
        self, interaction: discord.Interaction
    ) -> list[app_commands.Choice[str]]:
        """Get leagues for autocomplete based on the user."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))
            if not user:
                return []

            league_service = LeagueService(db)
            leagues = await league_service.get_user_leagues(str(user.id))

            return [
                app_commands.Choice(name=league.name[:100], value=str(league.id))
                for league in leagues[:25]
            ]


def require_linked_account():
    """Decorator to require a linked account for a command."""

    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            if hasattr(self, "require_linked_user"):
                user = await self.require_linked_user(interaction)
                if not user:
                    return
                # Store user in kwargs for the command
                kwargs["_linked_user"] = user
            return await func(self, interaction, *args, **kwargs)

        return wrapper

    return decorator
