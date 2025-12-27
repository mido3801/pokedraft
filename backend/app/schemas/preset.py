from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PoolPresetBase(BaseModel):
    """Base schema for pool presets."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = False


class PoolPresetCreate(PoolPresetBase):
    """Schema for creating a preset."""

    # Full pokemon pool with points
    # Structure: { "pokemon_id": { "name": str, "points": int|null, "types": [...], ... } }
    pokemon_pool: dict


class PoolPresetUpdate(BaseModel):
    """Schema for updating a preset."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    pokemon_pool: Optional[dict] = None


class PoolPresetResponse(PoolPresetBase):
    """Response schema for a preset with full pool data."""

    id: UUID
    user_id: UUID
    pokemon_pool: dict
    pokemon_count: int
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True


class PoolPresetSummary(BaseModel):
    """Summary schema for listing presets (without full pool data)."""

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    pokemon_count: int
    is_public: bool
    created_at: datetime
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True
