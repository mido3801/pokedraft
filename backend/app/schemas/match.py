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
    team_a_id: Optional[UUID] = None
    team_b_id: Optional[UUID] = None
    team_a_name: Optional[str] = None
    team_b_name: Optional[str] = None
    winner_id: Optional[UUID] = None
    winner_name: Optional[str] = None
    is_tie: bool
    replay_url: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: Optional[datetime] = None
    created_at: datetime

    # Bracket-specific fields
    schedule_format: Optional[str] = None
    bracket_round: Optional[int] = None
    bracket_position: Optional[int] = None
    next_match_id: Optional[UUID] = None
    loser_next_match_id: Optional[UUID] = None
    seed_a: Optional[int] = None
    seed_b: Optional[int] = None
    is_bye: bool = False
    is_bracket_reset: bool = False
    round_name: Optional[str] = None  # Computed: "Finals", "Semifinals", etc.

    class Config:
        from_attributes = True


class BracketMatch(Match):
    """Extended match schema for bracket tournaments with additional display fields."""
    pass


class BracketState(BaseModel):
    """Complete bracket state for frontend rendering."""

    season_id: UUID
    format: str  # 'single_elimination' or 'double_elimination'
    team_count: int
    total_rounds: int
    winners_bracket: list[list[Match]]  # [round][matches in round]
    losers_bracket: Optional[list[list[Match]]] = None  # For double elim
    grand_finals: Optional[list[Match]] = None  # For double elim (may have 2 matches)
    champion_id: Optional[UUID] = None
    champion_name: Optional[str] = None


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

    format: str = "round_robin"  # round_robin, double_round_robin, single_elimination, double_elimination
    use_standings_seeding: bool = True  # Auto-seed from standings
    manual_seeds: Optional[list[UUID]] = None  # Team IDs in seed order (1st = top seed)
    include_bracket_reset: bool = True  # For double elim grand finals
