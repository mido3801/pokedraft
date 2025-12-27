"""
Authentication endpoints.

In production, authentication is handled via Supabase OAuth.
The dev-login endpoint is only available when DEV_MODE=True.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import jwt
from datetime import datetime, timedelta, timezone

from app.core.security import get_current_user, get_current_user_optional
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import not_found
from app.schemas.user import User, UserUpdate
from app.models.user import User as UserModel

router = APIRouter()


@router.post("/dev-login")
@router.post("/dev-login/{user_number}")
async def dev_login(user_number: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Development-only login - creates a test user and returns a JWT token.

    This endpoint is only available when DEV_MODE=True.
    In production, authentication should be handled via Supabase OAuth.

    Args:
        user_number: Which test user to login as (1-9). Defaults to 1.
    """
    if not settings.DEV_MODE:
        raise not_found("Endpoint")

    # Clamp user_number to valid range
    user_number = max(1, min(9, user_number))

    # Create or get dev user with unique ID based on user_number
    dev_user_id = f"00000000-0000-0000-0000-00000000000{user_number}"
    result = await db.execute(select(UserModel).where(UserModel.id == dev_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = UserModel(
            id=dev_user_id,
            email=f"testuser{user_number}@pokedraft.example.com",
            display_name=f"Test User {user_number}",
            avatar_url=None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate a JWT token that matches Supabase format
    now = datetime.now(timezone.utc)
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "user_metadata": {
            "full_name": user.display_name,
        },
        "aud": "authenticated",
        "exp": now + timedelta(days=settings.SESSION_EXPIRE_DAYS),
        "iat": now,
    }

    # Use SECRET_KEY for signing in dev mode
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
        }
    }


@router.get("/me", response_model=Optional[User])
async def get_current_user_info(current_user=Depends(get_current_user_optional)):
    """Get current user info, or null if not authenticated."""
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    update: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    if update.display_name is not None:
        current_user.display_name = update.display_name
    if update.avatar_url is not None:
        current_user.avatar_url = update.avatar_url

    await db.commit()
    await db.refresh(current_user)

    return current_user
