from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.season import SeasonStatus


class SeasonSettings(BaseModel):
    """Season-specific settings (overrides league defaults)."""

    draft_format: Optional[str] = None
    roster_size: Optional[int] = None
    timer_seconds: Optional[int] = None
    budget_enabled: Optional[bool] = None
    budget_per_team: Optional[int] = None
    schedule_format: Optional[str] = None


class SeasonBase(BaseModel):
    """Base season schema."""

    keep_teams: bool = False


class SeasonCreate(SeasonBase):
    """Schema for creating a season."""

    settings: SeasonSettings = SeasonSettings()


class Season(SeasonBase):
    """Season response schema."""

    id: UUID
    league_id: UUID
    season_number: int
    status: SeasonStatus
    settings: dict
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    team_count: Optional[int] = None

    class Config:
        from_attributes = True
