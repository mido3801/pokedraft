from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import uuid4
import jwt
from datetime import datetime, timedelta

from app.core.security import get_current_user, get_current_user_optional
from app.core.config import settings
from app.core.database import get_db
from app.schemas.user import User, UserUpdate
from app.models.user import User as UserModel

router = APIRouter()


@router.post("/login")
async def login():
    """OAuth callback - exchange code for session."""
    # TODO: Implement Supabase OAuth flow
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/dev-login")
async def dev_login(db: AsyncSession = Depends(get_db)):
    """Development-only login - creates a test user and returns a JWT token."""
    if not settings.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    # Create or get dev user
    dev_user_id = "00000000-0000-0000-0000-000000000001"
    from sqlalchemy import select
    result = await db.execute(select(UserModel).where(UserModel.id == dev_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = UserModel(
            id=dev_user_id,
            email="dev@pokedraft.example.com",
            display_name="Dev User",
            avatar_url=None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate a JWT token that matches Supabase format
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "user_metadata": {
            "full_name": user.display_name,
        },
        "aud": "authenticated",
        "exp": datetime.utcnow() + timedelta(days=settings.SESSION_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
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


@router.post("/logout")
async def logout(current_user=Depends(get_current_user)):
    """End the current session."""
    # TODO: Implement session termination
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/me", response_model=Optional[User])
async def get_current_user_info(current_user=Depends(get_current_user_optional)):
    """Get current user info, or null if not authenticated."""
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    update: UserUpdate,
    current_user=Depends(get_current_user),
):
    """Update current user's profile."""
    # TODO: Implement user update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )
