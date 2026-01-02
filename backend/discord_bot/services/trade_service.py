"""Trade service for Discord bot operations."""
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Trade, Team, TeamPokemon, Pokemon, Season
from app.models.trade import TradeStatus


class TradeService:
    """Service for trade-related operations in the Discord bot."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_trade_by_id(self, trade_id: str) -> Optional[Trade]:
        """Get a trade by its ID.

        Args:
            trade_id: The trade ID (UUID as string).

        Returns:
            The Trade if found, None otherwise.
        """
        try:
            trade_uuid = uuid.UUID(trade_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(Trade)
            .where(Trade.id == trade_uuid)
            .options(
                selectinload(Trade.season).selectinload(Season.league),
                selectinload(Trade.proposer_team).selectinload(Team.user),
                selectinload(Trade.recipient_team).selectinload(Team.user),
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_trades_for_season(self, season_id: str) -> list[Trade]:
        """Get all pending trades in a season.

        Args:
            season_id: The season ID.

        Returns:
            List of pending trades.
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(Trade)
            .where(Trade.season_id == season_uuid)
            .where(Trade.status == TradeStatus.PENDING)
            .options(
                selectinload(Trade.proposer_team).selectinload(Team.user),
                selectinload(Trade.recipient_team).selectinload(Team.user),
            )
            .order_by(Trade.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_trades_for_team(
        self, team_id: str, status: Optional[TradeStatus] = None
    ) -> list[Trade]:
        """Get trades involving a team.

        Args:
            team_id: The team ID.
            status: Optional status filter.

        Returns:
            List of trades.
        """
        team_uuid = uuid.UUID(team_id)

        query = select(Trade).where(
            (Trade.proposer_team_id == team_uuid) | (Trade.recipient_team_id == team_uuid)
        )

        if status:
            query = query.where(Trade.status == status)

        query = query.options(
            selectinload(Trade.proposer_team).selectinload(Team.user),
            selectinload(Trade.recipient_team).selectinload(Team.user),
        ).order_by(Trade.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_incoming_trades_for_user(
        self, user_id: str, season_id: str
    ) -> list[Trade]:
        """Get pending trades where the user needs to respond.

        Args:
            user_id: The user ID.
            season_id: The season ID.

        Returns:
            List of incoming pending trades.
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
            select(Trade)
            .where(Trade.season_id == season_uuid)
            .where(Trade.recipient_team_id == team.id)
            .where(Trade.status == TradeStatus.PENDING)
            .options(
                selectinload(Trade.proposer_team).selectinload(Team.user),
                selectinload(Trade.recipient_team).selectinload(Team.user),
            )
            .order_by(Trade.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_trade_pokemon_details(
        self, trade: Trade
    ) -> tuple[list[tuple[TeamPokemon, Pokemon]], list[tuple[TeamPokemon, Pokemon]]]:
        """Get Pokemon details for a trade.

        Args:
            trade: The Trade object.

        Returns:
            Tuple of (proposer_pokemon_list, recipient_pokemon_list).
        """
        async def get_pokemon_list(team_pokemon_ids: list) -> list[tuple[TeamPokemon, Pokemon]]:
            if not team_pokemon_ids:
                return []

            result_list = []
            for tp_id in team_pokemon_ids:
                tp_result = await self.db.execute(
                    select(TeamPokemon).where(TeamPokemon.id == tp_id)
                )
                tp = tp_result.scalar_one_or_none()
                if tp:
                    pokemon_result = await self.db.execute(
                        select(Pokemon).where(Pokemon.id == tp.pokemon_id)
                    )
                    pokemon = pokemon_result.scalar_one_or_none()
                    if pokemon:
                        result_list.append((tp, pokemon))
            return result_list

        proposer_pokemon = await get_pokemon_list(trade.proposer_pokemon or [])
        recipient_pokemon = await get_pokemon_list(trade.recipient_pokemon or [])

        return (proposer_pokemon, recipient_pokemon)

    async def get_teams_in_season(self, season_id: str) -> list[Team]:
        """Get all teams in a season (for trade partner selection).

        Args:
            season_id: The season ID.

        Returns:
            List of teams.
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(Team)
            .where(Team.season_id == season_uuid)
            .options(selectinload(Team.user))
            .order_by(Team.display_name)
        )
        return list(result.scalars().all())

    async def can_user_respond_to_trade(
        self, trade_id: str, user_id: str
    ) -> tuple[bool, str]:
        """Check if a user can respond to a trade.

        Args:
            trade_id: The trade ID.
            user_id: The user ID.

        Returns:
            Tuple of (can_respond, reason).
        """
        trade = await self.get_trade_by_id(trade_id)
        if not trade:
            return (False, "Trade not found")

        if trade.status != TradeStatus.PENDING:
            return (False, f"Trade is already {trade.status.value}")

        user_uuid = uuid.UUID(user_id)

        # Check if user is the recipient
        if (
            trade.recipient_team
            and trade.recipient_team.user_id == user_uuid
        ):
            return (True, "")

        return (False, "You are not the recipient of this trade")

    async def can_user_cancel_trade(
        self, trade_id: str, user_id: str
    ) -> tuple[bool, str]:
        """Check if a user can cancel a trade.

        Args:
            trade_id: The trade ID.
            user_id: The user ID.

        Returns:
            Tuple of (can_cancel, reason).
        """
        trade = await self.get_trade_by_id(trade_id)
        if not trade:
            return (False, "Trade not found")

        if trade.status != TradeStatus.PENDING:
            return (False, f"Trade is already {trade.status.value}")

        user_uuid = uuid.UUID(user_id)

        # Check if user is the proposer
        if (
            trade.proposer_team
            and trade.proposer_team.user_id == user_uuid
        ):
            return (True, "")

        return (False, "You are not the proposer of this trade")

    async def get_trades_awaiting_admin_approval(
        self, season_id: str
    ) -> list[Trade]:
        """Get trades that need admin approval.

        Args:
            season_id: The season ID.

        Returns:
            List of trades awaiting admin approval.
        """
        season_uuid = uuid.UUID(season_id)

        result = await self.db.execute(
            select(Trade)
            .where(Trade.season_id == season_uuid)
            .where(Trade.status == TradeStatus.ACCEPTED)
            .where(Trade.requires_approval == True)
            .where(Trade.admin_approved.is_(None))
            .options(
                selectinload(Trade.proposer_team).selectinload(Team.user),
                selectinload(Trade.recipient_team).selectinload(Team.user),
            )
            .order_by(Trade.resolved_at.desc())
        )
        return list(result.scalars().all())
