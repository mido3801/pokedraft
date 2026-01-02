"""Configuration constants for the Discord bot."""
import os
from typing import Optional

# Bot token from environment
DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")

# Application URLs
APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:3000")
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

# Bot command prefix (for legacy text commands, if needed)
COMMAND_PREFIX: str = "!draft "

# Embed colors (Discord color format)
class Colors:
    """Discord embed colors."""

    PRIMARY = 0x5865F2  # Discord blurple
    SUCCESS = 0x57F287  # Green
    WARNING = 0xFEE75C  # Yellow
    ERROR = 0xED4245  # Red
    INFO = 0x5865F2  # Blurple

    # Feature-specific colors
    DRAFT = 0x3498DB  # Blue
    TRADE = 0x9B59B6  # Purple
    WAIVER = 0xE67E22  # Orange
    MATCH = 0x2ECC71  # Green
    POKEMON = 0xFFCB05  # Pokemon yellow


# Timeout values (in seconds)
class Timeouts:
    """Timeout values for bot interactions."""

    CONFIRMATION_VIEW = 300  # 5 minutes
    LEAGUE_SELECT_VIEW = 60  # 1 minute
    TRADE_WIZARD_VIEW = 600  # 10 minutes
    WAIVER_WIZARD_VIEW = 300  # 5 minutes


# Pagination
class Pagination:
    """Pagination settings."""

    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 25
    ROSTER_PAGE_SIZE = 6  # Pokemon per page
    PICKS_PAGE_SIZE = 10  # Draft picks per page


# Background task intervals (in seconds)
class TaskIntervals:
    """Background task intervals."""

    REMINDER_SCHEDULER = 900  # 15 minutes
    REMINDER_SENDER = 60  # 1 minute
    CLEANUP_OLD_REMINDERS = 86400  # 24 hours


# Reminder defaults
class ReminderDefaults:
    """Default values for reminders."""

    MATCH_REMINDER_HOURS = 24
    DRAFT_REMINDER_MINUTES = 30
    RESULT_DUE_REMINDER_HOURS = 24


# League settings keys (for JSONB settings field)
class LeagueDiscordSettings:
    """Keys for Discord-related league settings."""

    MATCH_REMINDER_ENABLED = "discord_match_reminder_enabled"
    MATCH_REMINDER_HOURS = "discord_match_reminder_hours"
    RESULT_DUE_REMINDER_ENABLED = "discord_result_due_reminder_enabled"
    RESULT_DUE_REMINDER_HOURS = "discord_result_due_reminder_hours"
    DRAFT_NOTIFICATIONS_ENABLED = "discord_draft_notifications_enabled"
    TRADE_NOTIFICATIONS_ENABLED = "discord_trade_notifications_enabled"
    WAIVER_NOTIFICATIONS_ENABLED = "discord_waiver_notifications_enabled"


# Sprite URLs
SPRITE_BASE_URL: str = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"
OFFICIAL_ARTWORK_URL: str = f"{SPRITE_BASE_URL}/other/official-artwork"


def get_pokemon_sprite(pokemon_id: int, style: str = "official") -> str:
    """Get the sprite URL for a Pokemon.

    Args:
        pokemon_id: The PokeAPI Pokemon ID
        style: Sprite style - "official" or "default"

    Returns:
        URL to the Pokemon sprite
    """
    if style == "official":
        return f"{OFFICIAL_ARTWORK_URL}/{pokemon_id}.png"
    return f"{SPRITE_BASE_URL}/{pokemon_id}.png"


def get_app_url(path: str = "") -> str:
    """Get a full URL to the web application.

    Args:
        path: The path to append (e.g., "/leagues/123")

    Returns:
        Full URL
    """
    return f"{APP_BASE_URL}{path}"
