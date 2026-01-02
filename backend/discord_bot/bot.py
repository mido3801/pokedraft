"""PokeDraft Discord Bot - Main entry point."""
import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands

from discord_bot.config import DISCORD_BOT_TOKEN, COMMAND_PREFIX
from discord_bot.notifications import NotificationService

logger = logging.getLogger(__name__)

# List of cog modules to load
COGS = [
    # Account & Info
    "discord_bot.cogs.account_commands",
    "discord_bot.cogs.league_commands",
    "discord_bot.cogs.team_commands",
    "discord_bot.cogs.pokemon_commands",
    # Draft
    "discord_bot.cogs.draft_commands",
    # Trades & Waivers
    "discord_bot.cogs.trade_commands",
    "discord_bot.cogs.waiver_commands",
    # Matches
    "discord_bot.cogs.match_commands",
    # Admin
    "discord_bot.cogs.admin_commands",
    # Background Tasks
    "discord_bot.tasks.reminder_tasks",
]


class PokeDraftBot(commands.Bot):
    """
    Pokemon Draft League Discord Bot.

    Provides commands and notifications for:
    - Account linking and settings
    - League, team, and Pokemon information
    - Draft events and picks
    - Trade proposals and completions
    - Waiver claims
    - Match reminders and results
    """

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True  # For DM notifications

        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            description="Pokemon Draft League Bot",
        )

        self.notification_service = NotificationService(self)

    async def setup_hook(self):
        """Called when the bot is ready to start."""
        logger.info("Setting up bot...")

        # Load all cogs
        for cog in COGS:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

        # Sync commands with Discord
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Called when the bot is connected and ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info("------")

        # Set presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Pokemon Draft Leagues",
            )
        )

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands

        logger.error(f"Command error: {error}", exc_info=error)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        """Handle application command errors."""
        logger.error(f"App command error: {error}", exc_info=error)

        error_message = "An error occurred while processing your command."

        if isinstance(error, discord.app_commands.CommandOnCooldown):
            error_message = f"Command on cooldown. Try again in {error.retry_after:.1f}s"
        elif isinstance(error, discord.app_commands.MissingPermissions):
            error_message = "You don't have permission to use this command."
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            error_message = "I don't have permission to do that."

        embed = discord.Embed(
            title="Error",
            description=error_message,
            color=discord.Color.red(),
        )

        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            pass


def setup_logging():
    """Set up logging for the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )

    # Reduce noise from discord.py
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)


async def run_bot_async():
    """Run the bot asynchronously."""
    setup_logging()

    token = DISCORD_BOT_TOKEN or os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN environment variable not set")

    bot = PokeDraftBot()

    async with bot:
        await bot.start(token)


def run_bot():
    """Run the Discord bot."""
    asyncio.run(run_bot_async())


if __name__ == "__main__":
    run_bot()
