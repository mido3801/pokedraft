"""Background tasks for scheduling and sending reminders."""
import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

from discord_bot.config import (
    Colors,
    TaskIntervals,
    ReminderDefaults,
    LeagueDiscordSettings,
    get_app_url,
    get_pokemon_sprite,
)
from discord_bot.database import get_db_session
from discord_bot.services.match_service import MatchService
from discord_bot.services.league_service import LeagueService
from discord_bot.services.user_service import UserService

from app.models import (
    ScheduledReminder,
    UserNotificationSettings,
    DiscordGuildConfig,
    Match,
    User,
)
from app.models.discord import ReminderType
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class ReminderTasks(commands.Cog):
    """Background tasks for scheduling and sending reminders."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Start tasks when cog is loaded."""
        self.schedule_reminders.start()
        self.send_reminders.start()
        self.cleanup_old_reminders.start()
        logger.info("Reminder tasks started")

    async def cog_unload(self):
        """Stop tasks when cog is unloaded."""
        self.schedule_reminders.cancel()
        self.send_reminders.cancel()
        self.cleanup_old_reminders.cancel()
        logger.info("Reminder tasks stopped")

    @tasks.loop(seconds=TaskIntervals.REMINDER_SCHEDULER)
    async def schedule_reminders(self):
        """Schedule reminders for upcoming matches and drafts."""
        try:
            await self._schedule_match_reminders()
        except Exception as e:
            logger.error(f"Error scheduling reminders: {e}", exc_info=True)

    @schedule_reminders.before_loop
    async def before_schedule_reminders(self):
        """Wait for bot to be ready before starting scheduler."""
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=TaskIntervals.REMINDER_SENDER)
    async def send_reminders(self):
        """Send due reminders."""
        try:
            await self._send_due_reminders()
        except Exception as e:
            logger.error(f"Error sending reminders: {e}", exc_info=True)

    @send_reminders.before_loop
    async def before_send_reminders(self):
        """Wait for bot to be ready before starting sender."""
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=TaskIntervals.CLEANUP_OLD_REMINDERS)
    async def cleanup_old_reminders(self):
        """Clean up old sent reminders."""
        try:
            await self._cleanup_old_reminders()
        except Exception as e:
            logger.error(f"Error cleaning up reminders: {e}", exc_info=True)

    @cleanup_old_reminders.before_loop
    async def before_cleanup(self):
        """Wait for bot to be ready before starting cleanup."""
        await self.bot.wait_until_ready()

    async def _schedule_match_reminders(self):
        """Schedule reminders for upcoming matches."""
        async with get_db_session() as db:
            match_service = MatchService(db)

            # Get matches starting in the next 48 hours
            matches = await match_service.get_matches_starting_soon(hours=48)

            for match in matches:
                await self._schedule_personal_reminders(db, match)
                await self._schedule_league_reminder(db, match)

    async def _schedule_personal_reminders(self, db, match: Match):
        """Schedule personal DM reminders for match participants."""
        if not match.team_a or not match.team_b:
            return

        # Get both users
        users = []
        if match.team_a.user:
            users.append((match.team_a.user, match.team_a))
        if match.team_b.user:
            users.append((match.team_b.user, match.team_b))

        for user, team in users:
            if not user.discord_id:
                continue

            # Get user's notification settings
            result = await db.execute(
                select(UserNotificationSettings).where(
                    UserNotificationSettings.user_id == user.id
                )
            )
            settings = result.scalar_one_or_none()

            if settings and not settings.dm_match_reminders:
                continue

            hours_before = (
                settings.match_reminder_hours_before
                if settings
                else ReminderDefaults.MATCH_REMINDER_HOURS
            )

            if not match.scheduled_at:
                continue

            scheduled_for = match.scheduled_at - timedelta(hours=hours_before)

            # Check if reminder already scheduled
            existing = await db.execute(
                select(ScheduledReminder)
                .where(ScheduledReminder.reminder_type == ReminderType.MATCH_PERSONAL)
                .where(ScheduledReminder.target_id == match.id)
                .where(ScheduledReminder.target_user_id == user.id)
            )
            if existing.scalar_one_or_none():
                continue

            # Create reminder
            reminder = ScheduledReminder(
                reminder_type=ReminderType.MATCH_PERSONAL,
                target_id=match.id,
                target_user_id=user.id,
                scheduled_for=scheduled_for,
            )
            db.add(reminder)

        await db.commit()

    async def _schedule_league_reminder(self, db, match: Match):
        """Schedule league channel reminder for a match."""
        if not match.season or not match.season.league:
            return

        if not match.scheduled_at:
            return

        league = match.season.league

        # Check league settings for reminders
        settings = league.settings or {}
        if not settings.get(LeagueDiscordSettings.MATCH_REMINDER_ENABLED, True):
            return

        hours = settings.get(
            LeagueDiscordSettings.MATCH_REMINDER_HOURS,
            ReminderDefaults.MATCH_REMINDER_HOURS,
        )

        scheduled_for = match.scheduled_at - timedelta(hours=hours)

        # Check if reminder already scheduled
        existing = await db.execute(
            select(ScheduledReminder)
            .where(ScheduledReminder.reminder_type == ReminderType.MATCH_LEAGUE)
            .where(ScheduledReminder.target_id == match.id)
            .where(ScheduledReminder.target_user_id.is_(None))
        )
        if existing.scalar_one_or_none():
            return

        # Create reminder
        reminder = ScheduledReminder(
            reminder_type=ReminderType.MATCH_LEAGUE,
            target_id=match.id,
            target_user_id=None,
            scheduled_for=scheduled_for,
        )
        db.add(reminder)
        await db.commit()

    async def _send_due_reminders(self):
        """Send all due reminders."""
        async with get_db_session() as db:
            now = datetime.utcnow()

            result = await db.execute(
                select(ScheduledReminder)
                .where(ScheduledReminder.scheduled_for <= now)
                .where(ScheduledReminder.sent_at.is_(None))
                .limit(50)
            )
            reminders = list(result.scalars().all())

            for reminder in reminders:
                try:
                    if reminder.reminder_type == ReminderType.MATCH_PERSONAL:
                        await self._send_personal_match_reminder(db, reminder)
                    elif reminder.reminder_type == ReminderType.MATCH_LEAGUE:
                        await self._send_league_match_reminder(db, reminder)

                    reminder.sent_at = datetime.utcnow()
                except Exception as e:
                    logger.error(f"Error sending reminder {reminder.id}: {e}")

            await db.commit()

    async def _send_personal_match_reminder(self, db, reminder: ScheduledReminder):
        """Send a personal DM match reminder."""
        if not reminder.target_user_id:
            return

        # Get user
        user_result = await db.execute(
            select(User).where(User.id == reminder.target_user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.discord_id:
            return

        # Get match
        match_service = MatchService(db)
        match = await match_service.get_match_by_id(str(reminder.target_id))
        if not match:
            return

        team_a_name = match.team_a.display_name if match.team_a else "TBD"
        team_b_name = match.team_b.display_name if match.team_b else "TBD"

        embed = discord.Embed(
            title="Match Reminder",
            description=f"**{team_a_name}** vs **{team_b_name}**",
            color=Colors.MATCH,
        )

        embed.add_field(name="Week", value=str(match.week), inline=True)

        if match.scheduled_at:
            embed.add_field(
                name="Time",
                value=f"<t:{int(match.scheduled_at.timestamp())}:R>",
                inline=True,
            )

        league_name = (
            match.season.league.name
            if match.season and match.season.league
            else "Unknown League"
        )
        embed.set_footer(text=f"League: {league_name}")

        try:
            discord_user = await self.bot.fetch_user(int(user.discord_id))
            await discord_user.send(embed=embed)
            logger.info(f"Sent match reminder to user {user.discord_id}")
        except discord.errors.Forbidden:
            logger.warning(f"Cannot DM user {user.discord_id} - DMs disabled")
        except Exception as e:
            logger.error(f"Failed to send DM to {user.discord_id}: {e}")

    async def _send_league_match_reminder(self, db, reminder: ScheduledReminder):
        """Send a league channel match reminder."""
        # Get match
        match_service = MatchService(db)
        match = await match_service.get_match_by_id(str(reminder.target_id))
        if not match or not match.season or not match.season.league:
            return

        league = match.season.league

        # Get guild config for this league
        result = await db.execute(
            select(DiscordGuildConfig)
            .where(DiscordGuildConfig.league_id == league.id)
            .where(DiscordGuildConfig.is_active == True)
        )
        configs = list(result.scalars().all())

        if not configs:
            return

        team_a_name = match.team_a.display_name if match.team_a else "TBD"
        team_b_name = match.team_b.display_name if match.team_b else "TBD"

        embed = discord.Embed(
            title="Match Starting Soon!",
            description=f"**{team_a_name}** vs **{team_b_name}**",
            color=Colors.MATCH,
        )

        embed.add_field(name="Week", value=str(match.week), inline=True)

        if match.scheduled_at:
            embed.add_field(
                name="Time",
                value=f"<t:{int(match.scheduled_at.timestamp())}:R>",
                inline=True,
            )

        # Mention participants
        mentions = []
        if match.team_a and match.team_a.user and match.team_a.user.discord_id:
            mentions.append(f"<@{match.team_a.user.discord_id}>")
        if match.team_b and match.team_b.user and match.team_b.user.discord_id:
            mentions.append(f"<@{match.team_b.user.discord_id}>")

        content = " ".join(mentions) if mentions else None

        for config in configs:
            channel_id = (
                config.match_reminder_channel_id or config.notification_channel_id
            )
            if not channel_id:
                continue

            try:
                channel = await self.bot.fetch_channel(int(channel_id))
                await channel.send(content=content, embed=embed)
                logger.info(f"Sent league match reminder to channel {channel_id}")
            except Exception as e:
                logger.error(f"Failed to send to channel {channel_id}: {e}")

    async def _cleanup_old_reminders(self):
        """Remove old sent reminders."""
        async with get_db_session() as db:
            cutoff = datetime.utcnow() - timedelta(days=7)

            result = await db.execute(
                select(ScheduledReminder)
                .where(ScheduledReminder.sent_at.is_not(None))
                .where(ScheduledReminder.sent_at < cutoff)
            )
            old_reminders = list(result.scalars().all())

            for reminder in old_reminders:
                await db.delete(reminder)

            if old_reminders:
                await db.commit()
                logger.info(f"Cleaned up {len(old_reminders)} old reminders")


async def setup(bot: commands.Bot):
    """Set up the reminder tasks cog."""
    await bot.add_cog(ReminderTasks(bot))
