"""Match service for Discord bot operations."""
import uuid
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Match, Team, Season


class MatchService:
    """Service for match-related operations in the Discord bot."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_match_by_id(self, match_id: str) -> Optional[Match]:
        """Get a match by its ID.

        Args:
            match_id: The match ID (UUID as string).

        Returns:
            The Match if found, None otherwise.
        """
        try:
            match_uuid = uuid.UUID(match_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(Match)
            .where(Match.id == match_uuid)
            .options(
                selectinload(Match.season).selectinload(Season.league),
                selectinload(Match.team_a).selectinload(Team.user),
                selectinload(Match.team_b).selectinload(Team.user),
                selectinload(Match.winner),
            )
        )
        return result.scalar_one_or_none()

    async def get_upcoming_matches_for_season(
        self, season_id: str, limit: int = 10
    ) -> list[Match]:
        """Get upcoming matches in a season.

        Args:
            season_id: The season ID.
            limit: Maximum matches to return.

        Returns:
            List of upcoming matches.
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(Match)
            .where(Match.season_id == season_uuid)
            .where(Match.winner_id.is_(None))
            .where(Match.is_tie == False)
            .where(Match.is_bye == False)
            .options(
                selectinload(Match.team_a).selectinload(Team.user),
                selectinload(Match.team_b).selectinload(Team.user),
            )
            .order_by(Match.week, Match.scheduled_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_matches_for_user(
        self,
        user_id: str,
        season_id: str,
        include_completed: bool = False,
    ) -> list[Match]:
        """Get matches involving a user's team.

        Args:
            user_id: The user ID.
            season_id: The season ID.
            include_completed: Whether to include completed matches.

        Returns:
            List of matches.
        """
        user_uuid = uuid.UUID(user_id)
        season_uuid = uuid.UUID(season_id)

        # Get user's team in this season
        team_result = await self.db.execute(
            select(Team)
            .where(Team.season_id == season_uuid)
            .where(Team.user_id == user_uuid)
        )
        team = team_result.scalar_one_or_none()
        if not team:
            return []

        query = (
            select(Match)
            .where(Match.season_id == season_uuid)
            .where(
                or_(Match.team_a_id == team.id, Match.team_b_id == team.id)
            )
            .options(
                selectinload(Match.team_a).selectinload(Team.user),
                selectinload(Match.team_b).selectinload(Team.user),
                selectinload(Match.winner),
            )
        )

        if not include_completed:
            query = query.where(Match.winner_id.is_(None)).where(Match.is_tie == False)

        query = query.order_by(Match.week, Match.scheduled_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_matches_needing_results(
        self, season_id: str
    ) -> list[Match]:
        """Get matches that are past their scheduled time without results.

        Args:
            season_id: The season ID.

        Returns:
            List of matches needing results.
        """
        season_uuid = uuid.UUID(season_id)
        now = datetime.utcnow()

        result = await self.db.execute(
            select(Match)
            .where(Match.season_id == season_uuid)
            .where(Match.winner_id.is_(None))
            .where(Match.is_tie == False)
            .where(Match.is_bye == False)
            .where(Match.scheduled_at < now)
            .options(
                selectinload(Match.team_a).selectinload(Team.user),
                selectinload(Match.team_b).selectinload(Team.user),
            )
            .order_by(Match.scheduled_at)
        )
        return list(result.scalars().all())

    async def get_matches_for_week(
        self, season_id: str, week: int
    ) -> list[Match]:
        """Get all matches for a specific week.

        Args:
            season_id: The season ID.
            week: The week number.

        Returns:
            List of matches for that week.
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(Match)
            .where(Match.season_id == season_uuid)
            .where(Match.week == week)
            .options(
                selectinload(Match.team_a).selectinload(Team.user),
                selectinload(Match.team_b).selectinload(Team.user),
                selectinload(Match.winner),
            )
            .order_by(Match.scheduled_at)
        )
        return list(result.scalars().all())

    async def can_user_report_result(
        self, match_id: str, user_id: str
    ) -> tuple[bool, str]:
        """Check if a user can report a match result.

        Args:
            match_id: The match ID.
            user_id: The user ID.

        Returns:
            Tuple of (can_report, reason).
        """
        match = await self.get_match_by_id(match_id)
        if not match:
            return (False, "Match not found")

        if match.winner_id or match.is_tie:
            return (False, "Match already has a result")

        user_uuid = uuid.UUID(user_id)

        # Check if user is one of the participants
        is_team_a = match.team_a and match.team_a.user_id == user_uuid
        is_team_b = match.team_b and match.team_b.user_id == user_uuid

        if not (is_team_a or is_team_b):
            return (False, "You are not a participant in this match")

        return (True, "")

    async def get_current_week(self, season_id: str) -> Optional[int]:
        """Determine the current week based on matches.

        Args:
            season_id: The season ID.

        Returns:
            Current week number, or None.
        """
        season_uuid = uuid.UUID(season_id)
        now = datetime.utcnow()

        # Find the week with upcoming matches
        result = await self.db.execute(
            select(Match.week)
            .where(Match.season_id == season_uuid)
            .where(Match.winner_id.is_(None))
            .where(Match.is_tie == False)
            .order_by(Match.week)
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None

    async def get_matches_starting_soon(
        self, hours: int = 24
    ) -> list[Match]:
        """Get matches starting within the specified hours.

        Args:
            hours: Hours from now to look ahead.

        Returns:
            List of matches starting soon.
        """
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=hours)

        result = await self.db.execute(
            select(Match)
            .where(Match.scheduled_at >= now)
            .where(Match.scheduled_at <= cutoff)
            .where(Match.winner_id.is_(None))
            .where(Match.is_tie == False)
            .where(Match.is_bye == False)
            .options(
                selectinload(Match.season).selectinload(Season.league),
                selectinload(Match.team_a).selectinload(Team.user),
                selectinload(Match.team_b).selectinload(Team.user),
            )
            .order_by(Match.scheduled_at)
        )
        return list(result.scalars().all())

    async def get_recent_results(
        self, season_id: str, limit: int = 10
    ) -> list[Match]:
        """Get recently completed matches.

        Args:
            season_id: The season ID.
            limit: Maximum matches to return.

        Returns:
            List of recent matches with results.
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(Match)
            .where(Match.season_id == season_uuid)
            .where(or_(Match.winner_id.is_not(None), Match.is_tie == True))
            .options(
                selectinload(Match.team_a).selectinload(Team.user),
                selectinload(Match.team_b).selectinload(Team.user),
                selectinload(Match.winner),
            )
            .order_by(Match.recorded_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
