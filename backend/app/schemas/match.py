from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MatchBase(BaseModel):
    """Base match schema."""

    week: int
    scheduled_at: Optional[datetime] = None


class MatchCreate(MatchBase):
    """Schema for creating a match."""

    team_a_id: UUID
    team_b_id: UUID


class MatchResult(BaseModel):
    """Schema for recording a match result."""

    winner_id: Optional[UUID] = None  # None for tie
    is_tie: bool = False
    replay_url: Optional[str] = None
    notes: Optional[str] = None


class Match(MatchBase):
    """Match response schema."""

    id: UUID
    season_id: UUID
    team_a_id: UUID
    team_b_id: UUID
    team_a_name: Optional[str] = None
    team_b_name: Optional[str] = None
    winner_id: Optional[UUID] = None
    winner_name: Optional[str] = None
    is_tie: bool
    replay_url: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TeamStanding(BaseModel):
    """A team's standing in the season."""

    team_id: UUID
    team_name: str
    wins: int
    losses: int
    ties: int
    points: int  # Calculated: wins * 3 + ties * 1
    games_played: int


class Standings(BaseModel):
    """Season standings."""

    season_id: UUID
    standings: list[TeamStanding]


class ScheduleGenerateRequest(BaseModel):
    """Request to generate a schedule."""

    format: str = "round_robin"  # round_robin, double_round_robin, swiss, etc.
