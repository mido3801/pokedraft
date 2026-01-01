import uuid
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WaiverClaimStatus(str, enum.Enum):
    """Waiver claim status enum."""

    PENDING = "pending"  # Claim submitted, waiting for processing
    APPROVED = "approved"  # Claim approved (executed or awaiting admin approval)
    REJECTED = "rejected"  # Claim rejected by admin
    CANCELLED = "cancelled"  # Claim cancelled by user
    EXPIRED = "expired"  # Claim expired (waiver period ended without processing)


class WaiverProcessingType(str, enum.Enum):
    """When waiver claims are processed."""

    IMMEDIATE = "immediate"  # Processed immediately when submitted
    NEXT_WEEK = "next_week"  # Processed at start of next week


class WaiverApprovalType(str, enum.Enum):
    """How waiver claims are approved."""

    NONE = "none"  # No approval needed - auto-approved
    ADMIN = "admin"  # League admin must approve
    LEAGUE_VOTE = "league_vote"  # League members vote on claims


class WaiverClaim(Base):
    """
    Waiver claim model - a request to add a free agent Pokemon to a team.

    This allows teams to pick up Pokemon that are not currently owned by any team
    in the season. The Pokemon being dropped (if any) goes back to the free agent pool.
    """

    __tablename__ = "waiver_claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id")
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id")
    )

    # Pokemon being claimed (PokeAPI ID - not currently owned by any team)
    pokemon_id: Mapped[int] = mapped_column(Integer)

    # Optional: Pokemon being dropped to make room (DraftPick UUID)
    drop_pokemon_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Claim status
    status: Mapped[WaiverClaimStatus] = mapped_column(
        Enum(WaiverClaimStatus, values_callable=lambda x: [e.value for e in x]),
        default=WaiverClaimStatus.PENDING
    )

    # Priority order (lower = higher priority, for waiver order systems)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Approval tracking
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Vote tracking (for league vote approval)
    votes_for: Mapped[int] = mapped_column(Integer, default=0)
    votes_against: Mapped[int] = mapped_column(Integer, default=0)
    votes_required: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Processing timing
    processing_type: Mapped[WaiverProcessingType] = mapped_column(
        Enum(WaiverProcessingType, values_callable=lambda x: [e.value for e in x]),
        default=WaiverProcessingType.IMMEDIATE
    )
    process_after: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Week tracking (for max changes per week)
    week_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    season = relationship("Season", back_populates="waiver_claims")
    team = relationship("Team", back_populates="waiver_claims")


class WaiverVote(Base):
    """
    Vote on a waiver claim (for league vote approval type).
    """

    __tablename__ = "waiver_votes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    waiver_claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("waiver_claims.id")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    vote: Mapped[bool] = mapped_column(Boolean)  # True = approve, False = reject
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    waiver_claim = relationship("WaiverClaim", backref="votes")
    user = relationship("User")
