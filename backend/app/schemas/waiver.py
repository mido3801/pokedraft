from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.waiver import WaiverClaimStatus, WaiverProcessingType


class WaiverClaimBase(BaseModel):
    """Base waiver claim schema."""

    pokemon_id: int = Field(..., description="PokeAPI ID of Pokemon to claim")
    drop_pokemon_id: Optional[UUID] = Field(
        None, description="DraftPick ID of Pokemon to drop (if required)"
    )


class WaiverClaimCreate(WaiverClaimBase):
    """Schema for creating a waiver claim."""

    pass


class WaiverClaimResponse(WaiverClaimBase):
    """Waiver claim response schema."""

    id: UUID
    season_id: UUID
    team_id: UUID
    team_name: Optional[str] = None
    status: WaiverClaimStatus
    priority: int
    requires_approval: bool
    admin_approved: Optional[bool] = None
    admin_notes: Optional[str] = None
    votes_for: int
    votes_against: int
    votes_required: Optional[int] = None
    processing_type: WaiverProcessingType
    process_after: Optional[datetime] = None
    week_number: Optional[int] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    # Enriched Pokemon data
    pokemon_name: Optional[str] = None
    pokemon_types: list[str] = []
    pokemon_sprite: Optional[str] = None
    drop_pokemon_name: Optional[str] = None
    drop_pokemon_types: list[str] = []

    class Config:
        from_attributes = True


class WaiverVoteCreate(BaseModel):
    """Schema for voting on a waiver claim."""

    vote: bool = Field(..., description="True to approve, False to reject")


class WaiverVoteResponse(BaseModel):
    """Waiver vote response schema."""

    id: UUID
    waiver_claim_id: UUID
    user_id: UUID
    vote: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WaiverAdminAction(BaseModel):
    """Schema for admin approval/rejection of a waiver claim."""

    approved: bool = Field(..., description="True to approve, False to reject")
    notes: Optional[str] = Field(None, max_length=500, description="Optional admin notes")


class WaiverClaimList(BaseModel):
    """Schema for listing waiver claims with pagination info."""

    claims: list[WaiverClaimResponse]
    total: int
    pending_count: int


class FreeAgentPokemon(BaseModel):
    """Schema for a Pokemon available as a free agent."""

    pokemon_id: int
    name: str
    types: list[str]
    sprite: Optional[str] = None
    base_stat_total: Optional[int] = None
    generation: Optional[int] = None


class FreeAgentList(BaseModel):
    """Schema for listing free agent Pokemon."""

    pokemon: list[FreeAgentPokemon]
    total: int
