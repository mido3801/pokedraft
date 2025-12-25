from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    display_name: str


class UserCreate(UserBase):
    """Schema for creating a user."""

    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class User(UserBase):
    """User response schema."""

    id: UUID
    avatar_url: Optional[str] = None
    discord_id: Optional[str] = None
    discord_username: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    """Public user info (for other users to see)."""

    id: UUID
    display_name: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
