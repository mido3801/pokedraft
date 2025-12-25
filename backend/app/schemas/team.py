from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.team import AcquisitionType


class TeamPokemon(BaseModel):
    """A Pokemon on a team."""

    id: UUID
    pokemon_id: int
    pokemon_name: str
    pick_number: Optional[int] = None
    acquisition_type: AcquisitionType
    points_spent: Optional[int] = None
    acquired_at: datetime
    # Pokemon data from PokeAPI
    types: list[str] = []
    sprite_url: Optional[str] = None

    class Config:
        from_attributes = True


class TeamBase(BaseModel):
    """Base team schema."""

    display_name: str = Field(..., min_length=1, max_length=100)


class TeamCreate(TeamBase):
    """Schema for creating a team."""

    pass


class Team(TeamBase):
    """Team response schema."""

    id: UUID
    season_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    draft_position: Optional[int] = None
    budget_remaining: Optional[int] = None
    wins: int
    losses: int
    ties: int
    created_at: datetime
    pokemon: list[TeamPokemon] = []

    class Config:
        from_attributes = True


class TeamExport(BaseModel):
    """Team export data."""

    team_name: str
    pokemon: list[dict]
    format: str = "showdown"  # showdown, json, csv


class ShowdownExport(BaseModel):
    """Pokemon Showdown paste format."""

    content: str
    filename: str
