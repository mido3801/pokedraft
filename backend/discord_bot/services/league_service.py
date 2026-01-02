"""League service for Discord bot operations."""
import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    League,
    LeagueMembership,
    Season,
    Team,
    DiscordGuildConfig,
)
from app.models.season import SeasonStatus


class LeagueService:
    """Service for league-related operations in the Discord bot."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_league_by_id(self, league_id: str) -> Optional[League]:
        """Get a league by its ID.

        Args:
            league_id: The league ID (UUID as string).

        Returns:
            The League if found, None otherwise.
        """
        try:
            league_uuid = uuid.UUID(league_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(League)
            .where(League.id == league_uuid)
            .options(
                selectinload(League.owner),
                selectinload(League.seasons),
            )
        )
        return result.scalar_one_or_none()

    async def get_league_by_invite_code(self, invite_code: str) -> Optional[League]:
        """Get a league by its invite code.

        Args:
            invite_code: The league invite code.

        Returns:
            The League if found, None otherwise.
        """
        result = await self.db.execute(
            select(League)
            .where(League.invite_code == invite_code)
            .options(selectinload(League.owner))
        )
        return result.scalar_one_or_none()

    async def get_user_leagues(self, user_id: str) -> list[League]:
        """Get all leagues a user is a member of.

        Args:
            user_id: The user ID (UUID as string).

        Returns:
            List of leagues the user is a member of.
        """
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return []

        result = await self.db.execute(
            select(League)
            .join(LeagueMembership, League.id == LeagueMembership.league_id)
            .where(LeagueMembership.user_id == user_uuid)
            .where(LeagueMembership.is_active == True)
            .options(selectinload(League.owner))
            .order_by(League.name)
        )
        return list(result.scalars().all())

    async def get_guild_default_league(self, guild_id: str) -> Optional[League]:
        """Get the default league for a Discord guild.

        If multiple leagues are configured for a guild, returns the first active one.

        Args:
            guild_id: The Discord guild ID.

        Returns:
            The default League for the guild, or None.
        """
        result = await self.db.execute(
            select(League)
            .join(DiscordGuildConfig, League.id == DiscordGuildConfig.league_id)
            .where(DiscordGuildConfig.guild_id == guild_id)
            .where(DiscordGuildConfig.is_active == True)
            .options(selectinload(League.owner))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_guild_leagues(self, guild_id: str) -> list[League]:
        """Get all leagues configured for a Discord guild.

        Args:
            guild_id: The Discord guild ID.

        Returns:
            List of leagues configured for the guild.
        """
        result = await self.db.execute(
            select(League)
            .join(DiscordGuildConfig, League.id == DiscordGuildConfig.league_id)
            .where(DiscordGuildConfig.guild_id == guild_id)
            .where(DiscordGuildConfig.is_active == True)
            .options(selectinload(League.owner))
        )
        return list(result.scalars().all())

    async def set_guild_league(
        self,
        guild_id: str,
        league_id: str,
        notification_channel_id: Optional[str] = None,
    ) -> DiscordGuildConfig:
        """Set or update a guild's league configuration.

        Args:
            guild_id: The Discord guild ID.
            league_id: The league ID to link.
            notification_channel_id: Optional channel for notifications.

        Returns:
            The created or updated DiscordGuildConfig.
        """
        league_uuid = uuid.UUID(league_id)

        # Check if config exists
        result = await self.db.execute(
            select(DiscordGuildConfig)
            .where(DiscordGuildConfig.guild_id == guild_id)
            .where(DiscordGuildConfig.league_id == league_uuid)
        )
        config = result.scalar_one_or_none()

        if config:
            config.is_active = True
            if notification_channel_id:
                config.notification_channel_id = notification_channel_id
        else:
            config = DiscordGuildConfig(
                guild_id=guild_id,
                league_id=league_uuid,
                notification_channel_id=notification_channel_id,
            )
            self.db.add(config)

        await self.db.flush()
        return config

    async def remove_guild_league(self, guild_id: str, league_id: str) -> bool:
        """Remove a league from a guild's configuration.

        Args:
            guild_id: The Discord guild ID.
            league_id: The league ID to unlink.

        Returns:
            True if removed, False if not found.
        """
        league_uuid = uuid.UUID(league_id)

        result = await self.db.execute(
            select(DiscordGuildConfig)
            .where(DiscordGuildConfig.guild_id == guild_id)
            .where(DiscordGuildConfig.league_id == league_uuid)
        )
        config = result.scalar_one_or_none()

        if config:
            config.is_active = False
            await self.db.flush()
            return True
        return False

    async def get_active_season(self, league_id: str) -> Optional[Season]:
        """Get the active season for a league.

        Args:
            league_id: The league ID.

        Returns:
            The active Season, or None if no active season.
        """
        league_uuid = uuid.UUID(league_id)

        result = await self.db.execute(
            select(Season)
            .where(Season.league_id == league_uuid)
            .where(Season.status.in_([SeasonStatus.DRAFTING, SeasonStatus.ACTIVE]))
            .options(
                selectinload(Season.teams),
                selectinload(Season.draft),
            )
            .order_by(Season.season_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_season_by_id(self, season_id: str) -> Optional[Season]:
        """Get a season by its ID.

        Args:
            season_id: The season ID.

        Returns:
            The Season if found, None otherwise.
        """
        try:
            season_uuid = uuid.UUID(season_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(Season)
            .where(Season.id == season_uuid)
            .options(
                selectinload(Season.league),
                selectinload(Season.teams),
                selectinload(Season.draft),
            )
        )
        return result.scalar_one_or_none()

    async def get_user_team_in_season(
        self, user_id: str, season_id: str
    ) -> Optional[Team]:
        """Get a user's team in a specific season.

        Args:
            user_id: The user ID.
            season_id: The season ID.

        Returns:
            The user's Team in that season, or None.
        """
        user_uuid = uuid.UUID(user_id)
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(Team)
            .where(Team.user_id == user_uuid)
            .where(Team.season_id == season_uuid)
            .options(selectinload(Team.pokemon))
        )
        return result.scalar_one_or_none()

    async def get_user_team_in_league(
        self, user_id: str, league_id: str
    ) -> Optional[Team]:
        """Get a user's team in the active season of a league.

        Args:
            user_id: The user ID.
            league_id: The league ID.

        Returns:
            The user's Team in the active season, or None.
        """
        season = await self.get_active_season(league_id)
        if not season:
            return None

        return await self.get_user_team_in_season(user_id, str(season.id))

    async def get_standings(self, season_id: str) -> list[Team]:
        """Get standings for a season.

        Args:
            season_id: The season ID.

        Returns:
            List of teams sorted by record (wins - losses).
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(Team)
            .where(Team.season_id == season_uuid)
            .options(selectinload(Team.user))
            .order_by(
                (Team.wins - Team.losses).desc(),
                Team.wins.desc(),
            )
        )
        return list(result.scalars().all())

    async def is_league_owner(self, user_id: str, league_id: str) -> bool:
        """Check if a user is the owner of a league.

        Args:
            user_id: The user ID.
            league_id: The league ID.

        Returns:
            True if the user is the league owner.
        """
        league = await self.get_league_by_id(league_id)
        if not league:
            return False

        user_uuid = uuid.UUID(user_id)
        return league.owner_id == user_uuid

    async def is_league_member(self, user_id: str, league_id: str) -> bool:
        """Check if a user is a member of a league.

        Args:
            user_id: The user ID.
            league_id: The league ID.

        Returns:
            True if the user is a league member.
        """
        user_uuid = uuid.UUID(user_id)
        league_uuid = uuid.UUID(league_id)

        result = await self.db.execute(
            select(func.count())
            .select_from(LeagueMembership)
            .where(LeagueMembership.user_id == user_uuid)
            .where(LeagueMembership.league_id == league_uuid)
            .where(LeagueMembership.is_active == True)
        )
        count = result.scalar()
        return count > 0

    async def get_league_discord_setting(
        self, league_id: str, setting_key: str, default=None
    ):
        """Get a Discord-related setting from league settings.

        Args:
            league_id: The league ID.
            setting_key: The setting key to retrieve.
            default: Default value if not set.

        Returns:
            The setting value, or default.
        """
        league = await self.get_league_by_id(league_id)
        if not league:
            return default

        return league.settings.get(setting_key, default)
