import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean
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
    team_a_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
    team_b_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
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

    # Bracket-specific fields
    schedule_format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # 'round_robin', 'single_elimination', 'double_elimination'

    bracket_round: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Positive = winners bracket round, Negative = losers bracket round, 0 = grand finals

    bracket_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Position within round for layout

    next_match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=True
    )
    # Match winner advances to

    loser_next_match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=True
    )
    # For double elim: losers bracket match

    seed_a: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    seed_b: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    is_bye: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bracket_reset: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    season = relationship("Season", back_populates="matches")
    team_a = relationship("Team", foreign_keys=[team_a_id])
    team_b = relationship("Team", foreign_keys=[team_b_id])
    winner = relationship("Team", foreign_keys=[winner_id])
    next_match = relationship("Match", foreign_keys=[next_match_id], remote_side=[id])
    loser_next_match = relationship("Match", foreign_keys=[loser_next_match_id], remote_side=[id])
