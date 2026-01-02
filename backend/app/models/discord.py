import uuid
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReminderType(str, PyEnum):
    """Types of scheduled reminders."""

    MATCH_PERSONAL = "match_personal"
    MATCH_LEAGUE = "match_league"
    DRAFT_STARTING = "draft_starting"
    WAIVER_DEADLINE = "waiver_deadline"


class DiscordGuildConfig(Base):
    """Configuration for linking Discord guilds to leagues."""

    __tablename__ = "discord_guild_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    guild_id: Mapped[str] = mapped_column(String(50), index=True)
    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False
    )
    notification_channel_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    match_reminder_channel_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    league = relationship("League", back_populates="discord_configs")

    __table_args__ = (
        # Unique constraint on guild_id + league_id
        {"sqlite_autoincrement": True},
    )


class UserNotificationSettings(Base):
    """Per-user notification preferences for Discord."""

    __tablename__ = "user_notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )

    # DM notification preferences
    dm_match_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    dm_trade_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    dm_waiver_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    dm_draft_notifications: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timing preferences
    match_reminder_hours_before: Mapped[int] = mapped_column(Integer, default=24)

    # Confirmation preferences
    require_confirmation_for_trades: Mapped[bool] = mapped_column(Boolean, default=True)
    require_confirmation_for_waivers: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="notification_settings")


class ScheduledReminder(Base):
    """Track scheduled reminders to prevent duplicates."""

    __tablename__ = "scheduled_reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reminder_type: Mapped[str] = mapped_column(
        Enum(ReminderType, name="remindertype", create_constraint=True),
        nullable=False,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )  # match_id, draft_id, or season_id
    target_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # For personal reminders
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    target_user = relationship("User")
