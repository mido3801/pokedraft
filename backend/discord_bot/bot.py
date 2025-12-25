import discord
from discord.ext import commands
from discord import app_commands
import os
from typing import Optional

from discord_bot.notifications import NotificationService


class PokeDraftBot(commands.Bot):
    """
    Pokemon Draft League Discord Bot.

    Provides notifications for:
    - Draft events (starting, your turn, picks made)
    - Trade proposals and completions
    - Match reminders and results
    """

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!draft ",
            intents=intents,
            description="Pokemon Draft League Bot",
        )

        self.notification_service = NotificationService(self)

    async def setup_hook(self):
        """Called when the bot is ready to start."""
        # Register slash commands
        await self.add_cog(DraftCommands(self))
        await self.add_cog(LeagueCommands(self))

        # Sync commands with Discord
        await self.tree.sync()
        print(f"Synced {len(self.tree.get_commands())} commands")

    async def on_ready(self):
        """Called when the bot is connected and ready."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")


class DraftCommands(commands.Cog):
    """Commands related to drafts."""

    def __init__(self, bot: PokeDraftBot):
        self.bot = bot

    @app_commands.command(name="draft", description="Get info about an active draft")
    async def draft_info(self, interaction: discord.Interaction, draft_id: Optional[str] = None):
        """Show information about the current or specified draft."""
        # TODO: Fetch draft info from API
        await interaction.response.send_message(
            "Draft info command not yet implemented.",
            ephemeral=True,
        )

    @app_commands.command(name="picks", description="Show recent picks in a draft")
    async def show_picks(self, interaction: discord.Interaction, count: int = 5):
        """Show the most recent picks in the draft."""
        # TODO: Fetch recent picks from API
        await interaction.response.send_message(
            "Picks command not yet implemented.",
            ephemeral=True,
        )

    @app_commands.command(name="available", description="Search available Pokemon")
    async def search_available(self, interaction: discord.Interaction, query: str):
        """Search for available Pokemon in the current draft."""
        # TODO: Search available Pokemon
        await interaction.response.send_message(
            f"Searching for '{query}'... (not yet implemented)",
            ephemeral=True,
        )


class LeagueCommands(commands.Cog):
    """Commands related to leagues."""

    def __init__(self, bot: PokeDraftBot):
        self.bot = bot

    @app_commands.command(name="standings", description="Show league standings")
    async def standings(self, interaction: discord.Interaction):
        """Show the current league standings."""
        # TODO: Fetch standings from API
        await interaction.response.send_message(
            "Standings command not yet implemented.",
            ephemeral=True,
        )

    @app_commands.command(name="schedule", description="Show upcoming matches")
    async def schedule(self, interaction: discord.Interaction, week: Optional[int] = None):
        """Show the schedule for the current or specified week."""
        # TODO: Fetch schedule from API
        await interaction.response.send_message(
            "Schedule command not yet implemented.",
            ephemeral=True,
        )

    @app_commands.command(name="team", description="Show a team's roster")
    async def team_roster(self, interaction: discord.Interaction, team_name: str):
        """Show a team's Pokemon roster."""
        # TODO: Fetch team roster from API
        await interaction.response.send_message(
            f"Team '{team_name}' roster... (not yet implemented)",
            ephemeral=True,
        )

    @app_commands.command(name="link", description="Link your Discord account")
    async def link_account(self, interaction: discord.Interaction):
        """Link your Discord account to the draft platform."""
        # TODO: Generate OAuth link
        await interaction.response.send_message(
            "To link your account, visit: https://yourdomain.com/auth/discord",
            ephemeral=True,
        )


def run_bot():
    """Run the Discord bot."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN environment variable not set")

    bot = PokeDraftBot()
    bot.run(token)


if __name__ == "__main__":
    run_bot()
