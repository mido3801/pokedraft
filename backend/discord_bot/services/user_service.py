"""User service for Discord bot operations."""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, UserNotificationSettings


class UserService:
    """Service for user-related operations in the Discord bot."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_discord_id(self, discord_id: str) -> Optional[User]:
        """Get a user by their Discord ID.

        Args:
            discord_id: The Discord user ID (as string).

        Returns:
            The User if found and linked, None otherwise.
        """
        result = await self.db.execute(
            select(User)
            .where(User.discord_id == discord_id)
            .where(User.is_active == True)
            .options(selectinload(User.notification_settings))
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by their PokeDraft user ID.

        Args:
            user_id: The PokeDraft user ID (UUID as string).

        Returns:
            The User if found, None otherwise.
        """
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(User)
            .where(User.id == user_uuid)
            .where(User.is_active == True)
            .options(selectinload(User.notification_settings))
        )
        return result.scalar_one_or_none()

    async def link_discord_account(
        self,
        user_id: str,
        discord_id: str,
        discord_username: str,
    ) -> Optional[User]:
        """Link a Discord account to a PokeDraft user.

        Args:
            user_id: The PokeDraft user ID.
            discord_id: The Discord user ID.
            discord_username: The Discord username.

        Returns:
            The updated User, or None if user not found.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Check if this Discord ID is already linked to another user
        existing = await self.get_user_by_discord_id(discord_id)
        if existing and existing.id != user.id:
            raise ValueError("This Discord account is already linked to another user")

        user.discord_id = discord_id
        user.discord_username = discord_username
        await self.db.flush()

        return user

    async def unlink_discord_account(self, user_id: str) -> Optional[User]:
        """Unlink a Discord account from a PokeDraft user.

        Args:
            user_id: The PokeDraft user ID.

        Returns:
            The updated User, or None if user not found.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        user.discord_id = None
        user.discord_username = None
        await self.db.flush()

        return user

    async def get_notification_settings(
        self, user_id: str
    ) -> Optional[UserNotificationSettings]:
        """Get notification settings for a user.

        Args:
            user_id: The PokeDraft user ID.

        Returns:
            The UserNotificationSettings if found, None otherwise.
        """
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(UserNotificationSettings).where(
                UserNotificationSettings.user_id == user_uuid
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_notification_settings(
        self, user_id: str
    ) -> UserNotificationSettings:
        """Get or create notification settings for a user.

        Args:
            user_id: The PokeDraft user ID.

        Returns:
            The UserNotificationSettings (existing or newly created).
        """
        settings = await self.get_notification_settings(user_id)
        if settings:
            return settings

        # Create default settings
        user_uuid = uuid.UUID(user_id)
        settings = UserNotificationSettings(user_id=user_uuid)
        self.db.add(settings)
        await self.db.flush()

        return settings

    async def update_notification_settings(
        self,
        user_id: str,
        **kwargs,
    ) -> Optional[UserNotificationSettings]:
        """Update notification settings for a user.

        Args:
            user_id: The PokeDraft user ID.
            **kwargs: Settings to update.

        Returns:
            The updated UserNotificationSettings, or None if user not found.
        """
        settings = await self.get_or_create_notification_settings(user_id)

        valid_fields = {
            "dm_match_reminders",
            "dm_trade_notifications",
            "dm_waiver_notifications",
            "dm_draft_notifications",
            "match_reminder_hours_before",
            "require_confirmation_for_trades",
            "require_confirmation_for_waivers",
        }

        for key, value in kwargs.items():
            if key in valid_fields:
                setattr(settings, key, value)

        await self.db.flush()
        return settings

    async def get_users_by_discord_ids(
        self, discord_ids: list[str]
    ) -> dict[str, User]:
        """Get multiple users by their Discord IDs.

        Args:
            discord_ids: List of Discord user IDs.

        Returns:
            Dict mapping discord_id to User.
        """
        if not discord_ids:
            return {}

        result = await self.db.execute(
            select(User)
            .where(User.discord_id.in_(discord_ids))
            .where(User.is_active == True)
        )
        users = result.scalars().all()

        return {user.discord_id: user for user in users if user.discord_id}
