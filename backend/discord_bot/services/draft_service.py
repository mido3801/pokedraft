"""Draft service for Discord bot operations."""
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Draft, DraftPick, Team, Pokemon, Season
from app.models.draft import DraftStatus


class DraftService:
    """Service for draft-related operations in the Discord bot."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_draft_by_id(self, draft_id: str) -> Optional[Draft]:
        """Get a draft by its ID.

        Args:
            draft_id: The draft ID (UUID as string).

        Returns:
            The Draft if found, None otherwise.
        """
        try:
            draft_uuid = uuid.UUID(draft_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(Draft)
            .where(Draft.id == draft_uuid)
            .options(
                selectinload(Draft.season).selectinload(Season.league),
                selectinload(Draft.picks),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_draft_for_season(self, season_id: str) -> Optional[Draft]:
        """Get the active draft for a season.

        Args:
            season_id: The season ID.

        Returns:
            The active Draft, or None if no active draft.
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(Draft)
            .where(Draft.season_id == season_uuid)
            .where(Draft.status.in_([DraftStatus.LIVE, DraftStatus.PAUSED]))
            .options(selectinload(Draft.picks))
        )
        return result.scalar_one_or_none()

    async def get_draft_for_league(self, league_id: str) -> Optional[Draft]:
        """Get the active draft for a league (via its active season).

        Args:
            league_id: The league ID.

        Returns:
            The active Draft, or None.
        """
        league_uuid = uuid.UUID(league_id)

        result = await self.db.execute(
            select(Draft)
            .join(Season, Draft.season_id == Season.id)
            .where(Season.league_id == league_uuid)
            .where(Draft.status.in_([DraftStatus.LIVE, DraftStatus.PAUSED]))
            .options(
                selectinload(Draft.season).selectinload(Season.league),
                selectinload(Draft.picks),
            )
        )
        return result.scalar_one_or_none()

    async def get_teams_in_draft(self, draft_id: str) -> list[Team]:
        """Get all teams participating in a draft.

        Args:
            draft_id: The draft ID.

        Returns:
            List of teams in draft order.
        """
        draft = await self.get_draft_by_id(draft_id)
        if not draft or not draft.season_id:
            return []

        result = await self.db.execute(
            select(Team)
            .where(Team.season_id == draft.season_id)
            .options(selectinload(Team.user))
            .order_by(Team.draft_position)
        )
        return list(result.scalars().all())

    async def get_current_picker(self, draft_id: str) -> Optional[Team]:
        """Get the team that is currently picking.

        Args:
            draft_id: The draft ID.

        Returns:
            The Team that should pick, or None.
        """
        draft = await self.get_draft_by_id(draft_id)
        if not draft or draft.status != DraftStatus.LIVE:
            return None

        if not draft.pick_order:
            return None

        # pick_order is a list of team_ids in pick order
        current_pick_index = draft.current_pick
        if current_pick_index >= len(draft.pick_order):
            return None

        team_id = draft.pick_order[current_pick_index]

        result = await self.db.execute(
            select(Team)
            .where(Team.id == uuid.UUID(team_id))
            .options(selectinload(Team.user))
        )
        return result.scalar_one_or_none()

    async def get_recent_picks(
        self, draft_id: str, limit: int = 10
    ) -> list[tuple[DraftPick, Team, Pokemon]]:
        """Get recent picks in a draft.

        Args:
            draft_id: The draft ID.
            limit: Maximum picks to return.

        Returns:
            List of (DraftPick, Team, Pokemon) tuples.
        """
        draft_uuid = uuid.UUID(draft_id)

        result = await self.db.execute(
            select(DraftPick)
            .where(DraftPick.draft_id == draft_uuid)
            .options(selectinload(DraftPick.team).selectinload(Team.user))
            .order_by(DraftPick.pick_number.desc())
            .limit(limit)
        )
        picks = list(result.scalars().all())

        # Get Pokemon data for each pick
        picks_with_data = []
        for pick in picks:
            pokemon_result = await self.db.execute(
                select(Pokemon).where(Pokemon.id == pick.pokemon_id)
            )
            pokemon = pokemon_result.scalar_one_or_none()
            if pokemon:
                picks_with_data.append((pick, pick.team, pokemon))

        return picks_with_data

    async def get_available_pokemon(
        self, draft_id: str, search: Optional[str] = None, limit: int = 25
    ) -> list[Pokemon]:
        """Get available Pokemon in a draft.

        Args:
            draft_id: The draft ID.
            search: Optional search query.
            limit: Maximum results.

        Returns:
            List of available Pokemon.
        """
        draft = await self.get_draft_by_id(draft_id)
        if not draft:
            return []

        # Get picked Pokemon IDs
        result = await self.db.execute(
            select(DraftPick.pokemon_id).where(DraftPick.draft_id == draft.id)
        )
        picked_ids = set(r[0] for r in result.all())

        # Build query for available Pokemon
        query = select(Pokemon)

        # Filter by pool if set
        if draft.pokemon_pool and draft.pokemon_pool.get("pokemon_ids"):
            pool_ids = draft.pokemon_pool["pokemon_ids"]
            query = query.where(Pokemon.id.in_(pool_ids))

        # Exclude picked Pokemon
        if picked_ids:
            query = query.where(~Pokemon.id.in_(picked_ids))

        # Search filter
        if search:
            query = query.where(Pokemon.identifier.ilike(f"%{search}%"))

        query = query.order_by(Pokemon.base_stat_total.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def is_users_turn(self, draft_id: str, user_id: str) -> bool:
        """Check if it's a user's turn to pick.

        Args:
            draft_id: The draft ID.
            user_id: The user ID.

        Returns:
            True if it's the user's turn.
        """
        current_picker = await self.get_current_picker(draft_id)
        if not current_picker or not current_picker.user:
            return False

        return str(current_picker.user_id) == user_id

    async def get_user_team_in_draft(
        self, draft_id: str, user_id: str
    ) -> Optional[Team]:
        """Get a user's team in a draft.

        Args:
            draft_id: The draft ID.
            user_id: The user ID.

        Returns:
            The user's Team in this draft, or None.
        """
        draft = await self.get_draft_by_id(draft_id)
        if not draft or not draft.season_id:
            return None

        user_uuid = uuid.UUID(user_id)

        result = await self.db.execute(
            select(Team)
            .where(Team.season_id == draft.season_id)
            .where(Team.user_id == user_uuid)
            .options(selectinload(Team.pokemon))
        )
        return result.scalar_one_or_none()

    async def get_draft_status_info(self, draft_id: str) -> dict:
        """Get comprehensive draft status information.

        Args:
            draft_id: The draft ID.

        Returns:
            Dict with draft status information.
        """
        draft = await self.get_draft_by_id(draft_id)
        if not draft:
            return {}

        teams = await self.get_teams_in_draft(draft_id)
        current_picker = await self.get_current_picker(draft_id)
        recent_picks = await self.get_recent_picks(draft_id, limit=5)

        total_picks = len(draft.pick_order) if draft.pick_order else 0
        picks_made = draft.current_pick

        return {
            "draft": draft,
            "status": draft.status.value,
            "format": draft.format.value,
            "teams": teams,
            "team_count": len(teams),
            "current_picker": current_picker,
            "picks_made": picks_made,
            "total_picks": total_picks,
            "roster_size": draft.roster_size,
            "timer_seconds": draft.timer_seconds,
            "recent_picks": recent_picks,
            "is_complete": draft.status == DraftStatus.COMPLETED,
            "league_name": (
                draft.season.league.name
                if draft.season and draft.season.league
                else None
            ),
        }

    async def get_picks_by_team(
        self, draft_id: str, team_id: str
    ) -> list[tuple[DraftPick, Pokemon]]:
        """Get all picks made by a team in a draft.

        Args:
            draft_id: The draft ID.
            team_id: The team ID.

        Returns:
            List of (DraftPick, Pokemon) tuples.
        """
        draft_uuid = uuid.UUID(draft_id)
        team_uuid = uuid.UUID(team_id)

        result = await self.db.execute(
            select(DraftPick)
            .where(DraftPick.draft_id == draft_uuid)
            .where(DraftPick.team_id == team_uuid)
            .order_by(DraftPick.pick_number)
        )
        picks = list(result.scalars().all())

        picks_with_pokemon = []
        for pick in picks:
            pokemon_result = await self.db.execute(
                select(Pokemon).where(Pokemon.id == pick.pokemon_id)
            )
            pokemon = pokemon_result.scalar_one_or_none()
            if pokemon:
                picks_with_pokemon.append((pick, pokemon))

        return picks_with_pokemon
