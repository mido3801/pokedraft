import uuid
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import String, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AcquisitionType(str, enum.Enum):
    """How a Pokemon was acquired."""

    DRAFTED = "drafted"
    TRADED = "traded"
    FREE_AGENT = "free_agent"


class Team(Base):
    """Team model - one participant's roster within a season."""

    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    season_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True
    )
    draft_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drafts.id"), nullable=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    # For anonymous users
    session_token: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    display_name: Mapped[str] = mapped_column(String(100))
    draft_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    budget_remaining: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    ties: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    season = relationship("Season", back_populates="teams")
    user = relationship("User", back_populates="teams")
    pokemon = relationship("TeamPokemon", back_populates="team")
    draft_picks = relationship("DraftPick", back_populates="team")


class TeamPokemon(Base):
    """Join table linking teams to their Pokemon."""

    __tablename__ = "team_pokemon"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))
    pokemon_id: Mapped[int] = mapped_column(Integer)  # PokeAPI Pokemon ID
    pick_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    acquisition_type: Mapped[AcquisitionType] = mapped_column(
        Enum(AcquisitionType), default=AcquisitionType.DRAFTED
    )
    points_spent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="pokemon")
