from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.draft import DraftFormat, DraftStatus


class PokemonPoolEntry(BaseModel):
    """A Pokemon in the draft pool."""

    pokemon_id: int
    name: str
    points: Optional[int] = None
    types: list[str] = []
    generation: Optional[int] = None


class DraftBase(BaseModel):
    """Base draft schema."""

    format: DraftFormat = DraftFormat.SNAKE
    timer_seconds: Optional[int] = 90
    budget_enabled: bool = False
    budget_per_team: Optional[int] = None
    roster_size: int = Field(default=6, ge=1, le=20)


class DraftCreate(DraftBase):
    """Schema for creating a draft."""

    pokemon_pool: list[PokemonPoolEntry] = []
    template_id: Optional[str] = None


class DraftPick(BaseModel):
    """A single draft pick."""

    pick_number: int
    team_id: UUID
    team_name: str
    pokemon_id: int
    pokemon_name: str
    points_spent: Optional[int] = None
    picked_at: datetime

    class Config:
        from_attributes = True


class DraftState(BaseModel):
    """Current state of a draft (for WebSocket sync)."""

    draft_id: UUID
    status: DraftStatus
    format: DraftFormat
    current_pick: int
    roster_size: int
    timer_seconds: Optional[int]
    timer_end: Optional[datetime] = None
    pick_order: list[UUID]
    teams: list[dict]
    picks: list[DraftPick]
    available_pokemon: list[PokemonPoolEntry]
    budget_enabled: bool
    budget_per_team: Optional[int] = None


class Draft(DraftBase):
    """Draft response schema."""

    id: UUID
    season_id: Optional[UUID] = None
    rejoin_code: Optional[str] = None
    status: DraftStatus
    current_pick: int
    pokemon_pool: dict
    pick_order: list
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnonymousDraftCreate(DraftBase):
    """Schema for creating an anonymous draft."""

    display_name: str = Field(..., min_length=1, max_length=50)
    pokemon_pool: list[PokemonPoolEntry] = []
    template_id: Optional[str] = None


class AnonymousDraftResponse(Draft):
    """Response for anonymous draft creation."""

    session_token: str
    rejoin_code: str
    join_url: str
