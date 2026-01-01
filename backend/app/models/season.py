import uuid
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SeasonStatus(str, enum.Enum):
    """Season status enum."""

    PRE_DRAFT = "pre_draft"
    DRAFTING = "drafting"
    ACTIVE = "active"
    COMPLETED = "completed"


class Season(Base):
    """Season model - one competitive cycle within a league."""

    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.id")
    )
    season_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[SeasonStatus] = mapped_column(
        Enum(SeasonStatus), default=SeasonStatus.PRE_DRAFT
    )
    keep_teams: Mapped[bool] = mapped_column(Boolean, default=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    league = relationship("League", back_populates="seasons")
    draft = relationship("Draft", back_populates="season", uselist=False)
    teams = relationship("Team", back_populates="season")
    matches = relationship("Match", back_populates="season")
    trades = relationship("Trade", back_populates="season")
    waiver_claims = relationship("WaiverClaim", back_populates="season")
