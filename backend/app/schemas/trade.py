from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.trade import TradeStatus


class TradeBase(BaseModel):
    """Base trade schema."""

    recipient_team_id: UUID
    proposer_pokemon: list[UUID]
    recipient_pokemon: list[UUID]
    message: Optional[str] = None


class TradeCreate(TradeBase):
    """Schema for creating a trade."""

    pass


class TradeResponse(BaseModel):
    """Schema for responding to a trade."""

    action: str  # accept, reject


class Trade(TradeBase):
    """Trade response schema."""

    id: UUID
    season_id: UUID
    proposer_team_id: UUID
    proposer_team_name: Optional[str] = None
    recipient_team_name: Optional[str] = None
    status: TradeStatus
    requires_approval: bool
    admin_approved: Optional[bool] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    # Pokemon details
    proposer_pokemon_details: list[dict] = []
    recipient_pokemon_details: list[dict] = []

    class Config:
        from_attributes = True
