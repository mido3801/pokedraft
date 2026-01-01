from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class LeagueSettings(BaseModel):
    """Default league settings."""

    draft_format: str = "snake"
    roster_size: int = 6
    timer_seconds: int = 90
    budget_enabled: bool = False
    budget_per_team: Optional[int] = None
    trade_approval_required: bool = False

    # Waiver wire / Free agent settings
    waiver_enabled: bool = False
    waiver_approval_type: Literal["none", "admin", "league_vote"] = "none"
    waiver_processing_type: Literal["immediate", "next_week"] = "immediate"
    waiver_max_per_week: Optional[int] = None  # None = unlimited
    waiver_require_drop: bool = False  # Must drop a Pokemon when claiming


class LeagueBase(BaseModel):
    """Base league schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class LeagueCreate(LeagueBase):
    """Schema for creating a league."""

    settings: LeagueSettings = LeagueSettings()
    template_id: Optional[str] = None


class LeagueUpdate(BaseModel):
    """Schema for updating a league."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    settings: Optional[LeagueSettings] = None


class League(LeagueBase):
    """League response schema."""

    id: UUID
    owner_id: UUID
    invite_code: str
    settings: dict
    created_at: datetime
    member_count: Optional[int] = None
    current_season: Optional[int] = None

    class Config:
        from_attributes = True


class LeagueInvite(BaseModel):
    """League invite info."""

    invite_code: str
    invite_url: str


class LeagueMember(BaseModel):
    """League member info."""

    user_id: UUID
    display_name: str
    avatar_url: Optional[str] = None
    joined_at: datetime

    class Config:
        from_attributes = True
