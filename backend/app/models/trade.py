import uuid
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TradeStatus(str, enum.Enum):
    """Trade status enum."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Trade(Base):
    """Trade model - a trade of Pokemon between two teams."""

    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id")
    )
    proposer_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id")
    )
    recipient_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id")
    )
    proposer_pokemon: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    recipient_pokemon: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    status: Mapped[TradeStatus] = mapped_column(Enum(TradeStatus), default=TradeStatus.PENDING)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    season = relationship("Season", back_populates="trades")
    proposer_team = relationship("Team", foreign_keys=[proposer_team_id])
    recipient_team = relationship("Team", foreign_keys=[recipient_team_id])
