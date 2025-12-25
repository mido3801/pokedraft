import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Match(Base):
    """Match model - a scheduled or completed match between two teams."""

    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id")
    )
    week: Mapped[int] = mapped_column(Integer)
    team_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))
    team_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
    is_tie: Mapped[bool] = mapped_column(default=False)
    replay_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    result_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    season = relationship("Season", back_populates="matches")
    team_a = relationship("Team", foreign_keys=[team_a_id])
    team_b = relationship("Team", foreign_keys=[team_b_id])
    winner = relationship("Team", foreign_keys=[winner_id])
