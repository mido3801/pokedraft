from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.core.security import get_current_user, get_current_user_optional
from app.schemas.user import User, UserUpdate

router = APIRouter()


@router.post("/login")
async def login():
    """OAuth callback - exchange code for session."""
    # TODO: Implement Supabase OAuth flow
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


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
