import uuid
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DraftFormat(str, enum.Enum):
    """Draft format enum."""

    SNAKE = "snake"
    LINEAR = "linear"
    AUCTION = "auction"


class DraftStatus(str, enum.Enum):
    """Draft status enum."""

    PENDING = "pending"
    LIVE = "live"
    PAUSED = "paused"
    COMPLETED = "completed"


class Draft(Base):
    """Draft model - the event where teams select Pokemon."""

    __tablename__ = "drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    season_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True
    )
    # For anonymous drafts without a season
    session_token: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    rejoin_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True)

    format: Mapped[DraftFormat] = mapped_column(Enum(DraftFormat), default=DraftFormat.SNAKE)
    timer_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=90)
    budget_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    budget_per_team: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    roster_size: Mapped[int] = mapped_column(Integer, default=6)
    # Auction-specific settings
    nomination_timer_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_bid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1)
    bid_increment: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1)
    status: Mapped[DraftStatus] = mapped_column(Enum(DraftStatus), default=DraftStatus.PENDING)
    current_pick: Mapped[int] = mapped_column(Integer, default=0)
    pokemon_pool: Mapped[dict] = mapped_column(JSONB, default=dict)
    pick_order: Mapped[list] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    season = relationship("Season", back_populates="draft")
    picks = relationship("DraftPick", back_populates="draft")


class DraftPick(Base):
    """Individual pick in a draft."""

    __tablename__ = "draft_picks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drafts.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))
    pokemon_id: Mapped[int] = mapped_column(Integer)  # PokeAPI Pokemon ID
    pick_number: Mapped[int] = mapped_column(Integer)
    points_spent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    picked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    draft = relationship("Draft", back_populates="picks")
    team = relationship("Team", back_populates="draft_picks")
