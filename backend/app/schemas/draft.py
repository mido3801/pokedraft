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


class PokemonFilters(BaseModel):
    """Filters to apply when building the Pokemon pool."""

    generations: list[int] = Field(
        default=[1, 2, 3, 4, 5, 6, 7, 8, 9],
        description="Which generations to include (1-9)"
    )
    evolution_stages: list[int] = Field(
        default=[0, 1, 2],
        description="Evolution stages to include: 0=unevolved, 1=middle, 2=fully evolved"
    )
    include_legendary: bool = Field(
        default=True,
        description="Include legendary Pokemon"
    )
    include_mythical: bool = Field(
        default=True,
        description="Include mythical Pokemon"
    )
    types: list[str] = Field(
        default=[],
        description="Filter by types (empty = all types allowed)"
    )
    bst_min: int = Field(
        default=0,
        ge=0,
        description="Minimum base stat total"
    )
    bst_max: int = Field(
        default=999,
        le=999,
        description="Maximum base stat total"
    )
    custom_exclusions: list[int] = Field(
        default=[],
        description="Pokemon IDs to exclude from the pool"
    )
    custom_inclusions: list[int] = Field(
        default=[],
        description="Pokemon IDs to force include (overrides other filters)"
    )


class DraftBase(BaseModel):
    """Base draft schema."""

    format: DraftFormat = DraftFormat.SNAKE
    timer_seconds: Optional[int] = 90
    budget_enabled: bool = False
    budget_per_team: Optional[int] = None
    roster_size: int = Field(default=6, ge=1, le=20)
    # Auction-specific settings
    nomination_timer_seconds: Optional[int] = None
    min_bid: Optional[int] = Field(default=1, ge=1)
    bid_increment: Optional[int] = Field(default=1, ge=1)


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
    # Auction-specific settings
    nomination_timer_seconds: Optional[int] = None
    min_bid: Optional[int] = None
    bid_increment: Optional[int] = None


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
    pokemon_filters: Optional[PokemonFilters] = None
    template_id: Optional[str] = None


class AnonymousDraftResponse(Draft):
    """Response for anonymous draft creation."""

    session_token: str
    rejoin_code: str
    join_url: str
    team_id: str
