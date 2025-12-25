import discord
from typing import Optional, List
from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications the bot can send."""

    DRAFT_STARTING = "draft_starting"
    YOUR_TURN = "your_turn"
    PICK_MADE = "pick_made"
    DRAFT_COMPLETE = "draft_complete"
    TRADE_PROPOSED = "trade_proposed"
    TRADE_COMPLETED = "trade_completed"
    MATCH_REMINDER = "match_reminder"
    MATCH_RESULT = "match_result"


class NotificationService:
    """
    Service for sending notifications via Discord.

    Handles both DM notifications to users and channel notifications for leagues.
    """

    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def send_dm(self, discord_user_id: int, embed: discord.Embed) -> bool:
        """Send a DM to a user."""
        try:
            user = await self.bot.fetch_user(discord_user_id)
            await user.send(embed=embed)
            return True
        except discord.errors.Forbidden:
            # User has DMs disabled
            return False
        except Exception as e:
            print(f"Error sending DM: {e}")
            return False

    async def send_channel_message(
        self,
        channel_id: int,
        embed: discord.Embed,
        mention_users: Optional[List[int]] = None,
    ) -> bool:
        """Send a message to a channel."""
        try:
            channel = await self.bot.fetch_channel(channel_id)
            content = None
            if mention_users:
                content = " ".join(f"<@{uid}>" for uid in mention_users)
            await channel.send(content=content, embed=embed)
            return True
        except Exception as e:
            print(f"Error sending channel message: {e}")
            return False

    # Notification builders

    def build_draft_starting_embed(
        self,
        league_name: str,
        draft_url: str,
        starts_in_minutes: int,
    ) -> discord.Embed:
        """Build embed for draft starting notification."""
        embed = discord.Embed(
            title="Draft Starting Soon!",
            description=f"The draft for **{league_name}** is starting in {starts_in_minutes} minutes!",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Join Now", value=f"[Click here to join]({draft_url})")
        return embed

    def build_your_turn_embed(
        self,
        league_name: str,
        draft_url: str,
        pick_number: int,
        time_remaining: int,
    ) -> discord.Embed:
        """Build embed for your turn notification."""
        embed = discord.Embed(
            title="It's Your Turn to Pick!",
            description=f"You're on the clock in **{league_name}**!",
            color=discord.Color.green(),
        )
        embed.add_field(name="Pick Number", value=str(pick_number), inline=True)
        embed.add_field(name="Time", value=f"{time_remaining}s", inline=True)
        embed.add_field(name="Draft", value=f"[Make your pick]({draft_url})", inline=False)
        return embed

    def build_pick_made_embed(
        self,
        team_name: str,
        pokemon_name: str,
        pokemon_sprite: str,
        pick_number: int,
    ) -> discord.Embed:
        """Build embed for pick made notification."""
        embed = discord.Embed(
            title="Pick Made!",
            description=f"**{team_name}** selected **{pokemon_name}**",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Pick #", value=str(pick_number))
        if pokemon_sprite:
            embed.set_thumbnail(url=pokemon_sprite)
        return embed

    def build_draft_complete_embed(
        self,
        league_name: str,
        teams_summary: List[dict],
    ) -> discord.Embed:
        """Build embed for draft complete notification."""
        embed = discord.Embed(
            title="Draft Complete!",
            description=f"The draft for **{league_name}** has finished!",
            color=discord.Color.gold(),
        )
        for team in teams_summary[:5]:  # Show first 5 teams
            pokemon_list = ", ".join(team["pokemon"][:3])
            if len(team["pokemon"]) > 3:
                pokemon_list += f" +{len(team['pokemon']) - 3} more"
            embed.add_field(
                name=team["name"],
                value=pokemon_list,
                inline=False,
            )
        return embed

    def build_trade_proposed_embed(
        self,
        proposer_team: str,
        recipient_team: str,
        proposer_pokemon: List[str],
        recipient_pokemon: List[str],
    ) -> discord.Embed:
        """Build embed for trade proposed notification."""
        embed = discord.Embed(
            title="Trade Proposal",
            description=f"**{proposer_team}** has proposed a trade!",
            color=discord.Color.purple(),
        )
        embed.add_field(
            name=f"{proposer_team} Offers",
            value="\n".join(proposer_pokemon) or "Nothing",
            inline=True,
        )
        embed.add_field(
            name=f"{recipient_team} Gives",
            value="\n".join(recipient_pokemon) or "Nothing",
            inline=True,
        )
        return embed

    def build_match_reminder_embed(
        self,
        team_a: str,
        team_b: str,
        scheduled_time: str,
        week: int,
    ) -> discord.Embed:
        """Build embed for match reminder notification."""
        embed = discord.Embed(
            title="Match Reminder",
            description=f"**{team_a}** vs **{team_b}**",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Week", value=str(week), inline=True)
        embed.add_field(name="Scheduled", value=scheduled_time, inline=True)
        return embed

    def build_match_result_embed(
        self,
        team_a: str,
        team_b: str,
        winner: Optional[str],
        is_tie: bool,
    ) -> discord.Embed:
        """Build embed for match result notification."""
        if is_tie:
            title = "Match Result: Tie!"
            description = f"**{team_a}** and **{team_b}** tied!"
        else:
            title = "Match Result"
            description = f"**{winner}** wins!"

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green(),
        )
        return embed
