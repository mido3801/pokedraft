"""Waiver service for Discord bot operations."""
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import select, and_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import WaiverClaim, Team, TeamPokemon, Pokemon, Season
from app.models.waiver import WaiverClaimStatus


class WaiverService:
    """Service for waiver-related operations in the Discord bot."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_waiver_by_id(self, waiver_id: str) -> Optional[WaiverClaim]:
        """Get a waiver claim by its ID.

        Args:
            waiver_id: The waiver claim ID (UUID as string).

        Returns:
            The WaiverClaim if found, None otherwise.
        """
        try:
            waiver_uuid = uuid.UUID(waiver_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(WaiverClaim)
            .where(WaiverClaim.id == waiver_uuid)
            .options(
                selectinload(WaiverClaim.season).selectinload(Season.league),
                selectinload(WaiverClaim.team).selectinload(Team.user),
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_waivers_for_season(
        self, season_id: str
    ) -> list[WaiverClaim]:
        """Get all pending waiver claims in a season.

        Args:
            season_id: The season ID.

        Returns:
            List of pending waiver claims.
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(WaiverClaim)
            .where(WaiverClaim.season_id == season_uuid)
            .where(WaiverClaim.status == WaiverClaimStatus.PENDING)
            .options(selectinload(WaiverClaim.team).selectinload(Team.user))
            .order_by(WaiverClaim.priority, WaiverClaim.created_at)
        )
        return list(result.scalars().all())

    async def get_waivers_for_user(
        self, user_id: str, season_id: str
    ) -> list[WaiverClaim]:
        """Get waiver claims submitted by a user.

        Args:
            user_id: The user ID.
            season_id: The season ID.

        Returns:
            List of user's waiver claims.
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

        result = await self.db.execute(
            select(WaiverClaim)
            .where(WaiverClaim.season_id == season_uuid)
            .where(WaiverClaim.team_id == team.id)
            .options(selectinload(WaiverClaim.team))
            .order_by(WaiverClaim.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_waiver_pokemon_details(
        self, waiver: WaiverClaim
    ) -> tuple[Optional[Pokemon], Optional[tuple[TeamPokemon, Pokemon]]]:
        """Get Pokemon details for a waiver claim.

        Args:
            waiver: The WaiverClaim object.

        Returns:
            Tuple of (claiming_pokemon, drop_pokemon_info).
        """
        # Get the Pokemon being claimed
        claiming_result = await self.db.execute(
            select(Pokemon).where(Pokemon.id == waiver.pokemon_id)
        )
        claiming_pokemon = claiming_result.scalar_one_or_none()

        # Get the Pokemon being dropped (if any)
        drop_info = None
        if waiver.drop_pokemon_id:
            tp_result = await self.db.execute(
                select(TeamPokemon).where(TeamPokemon.id == waiver.drop_pokemon_id)
            )
            tp = tp_result.scalar_one_or_none()
            if tp:
                drop_pokemon_result = await self.db.execute(
                    select(Pokemon).where(Pokemon.id == tp.pokemon_id)
                )
                drop_pokemon = drop_pokemon_result.scalar_one_or_none()
                if drop_pokemon:
                    drop_info = (tp, drop_pokemon)

        return (claiming_pokemon, drop_info)

    async def get_free_agents(
        self,
        season_id: str,
        search: Optional[str] = None,
        limit: int = 25,
    ) -> list[Pokemon]:
        """Get available free agents (Pokemon not owned by any team).

        Args:
            season_id: The season ID.
            search: Optional search query.
            limit: Maximum results.

        Returns:
            List of available Pokemon.
        """
        season_uuid = uuid.UUID(season_id)

        # Get all Pokemon IDs owned by teams in this season
        owned_result = await self.db.execute(
            select(TeamPokemon.pokemon_id)
            .join(Team, TeamPokemon.team_id == Team.id)
            .where(Team.season_id == season_uuid)
        )
        owned_ids = set(r[0] for r in owned_result.all())

        # Build query for free agents
        query = select(Pokemon)

        # Exclude owned Pokemon
        if owned_ids:
            query = query.where(~Pokemon.id.in_(owned_ids))

        # Search filter
        if search:
            query = query.where(Pokemon.identifier.ilike(f"%{search}%"))

        # Default Pokemon only
        query = query.where(Pokemon.is_default == True)
        query = query.order_by(Pokemon.base_stat_total.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def can_user_cancel_waiver(
        self, waiver_id: str, user_id: str
    ) -> tuple[bool, str]:
        """Check if a user can cancel a waiver claim.

        Args:
            waiver_id: The waiver claim ID.
            user_id: The user ID.

        Returns:
            Tuple of (can_cancel, reason).
        """
        waiver = await self.get_waiver_by_id(waiver_id)
        if not waiver:
            return (False, "Waiver claim not found")

        if waiver.status != WaiverClaimStatus.PENDING:
            return (False, f"Waiver claim is already {waiver.status.value}")

        user_uuid = uuid.UUID(user_id)

        # Check if user owns the team that made the claim
        if waiver.team and waiver.team.user_id == user_uuid:
            return (True, "")

        return (False, "You did not submit this waiver claim")

    async def get_waivers_awaiting_admin_approval(
        self, season_id: str
    ) -> list[WaiverClaim]:
        """Get waiver claims that need admin approval.

        Args:
            season_id: The season ID.

        Returns:
            List of waiver claims awaiting admin approval.
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(WaiverClaim)
            .where(WaiverClaim.season_id == season_uuid)
            .where(WaiverClaim.status == WaiverClaimStatus.PENDING)
            .where(WaiverClaim.requires_approval == True)
            .where(WaiverClaim.admin_approved.is_(None))
            .options(selectinload(WaiverClaim.team).selectinload(Team.user))
            .order_by(WaiverClaim.created_at)
        )
        return list(result.scalars().all())

    async def get_pending_waivers_count_for_user(
        self, user_id: str, season_id: str
    ) -> int:
        """Get count of pending waivers for a user.

        Args:
            user_id: The user ID.
            season_id: The season ID.

        Returns:
            Count of pending waiver claims.
        """
        waivers = await self.get_waivers_for_user(user_id, season_id)
        return sum(1 for w in waivers if w.status == WaiverClaimStatus.PENDING)
