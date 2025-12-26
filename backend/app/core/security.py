import secrets
from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt import PyJWTError

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

security = HTTPBearer(auto_error=False)


def generate_session_token() -> str:
    """Generate a secure session token for anonymous users."""
    return secrets.token_urlsafe(32)


def generate_rejoin_code() -> str:
    """Generate a memorable rejoin code (e.g., PIKA-7842)."""
    pokemon_prefixes = [
        "PIKA", "CHAR", "BULB", "SQRT", "EEVEE",
        "JIGG", "MEOW", "PSYD", "SLWP", "GENR",
    ]
    prefix = secrets.choice(pokemon_prefixes)
    number = secrets.randbelow(9000) + 1000
    return f"{prefix}-{number}"


def generate_invite_code() -> str:
    """Generate a league invite code."""
    return secrets.token_urlsafe(8)


def decode_supabase_token(token: str) -> Optional[dict]:
    """Decode and validate a Supabase JWT token."""
    try:
        # Supabase uses the JWT secret from the project settings
        # For development, we can decode without verification
        # In production, verify with SUPABASE_JWT_SECRET
        if settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            # Development mode - decode without verification
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
            )
        return payload
    except PyJWTError:
        return None


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_supabase_token(token)
    if payload is None:
        return None

    # Get user ID from Supabase token (sub claim)
    user_id = payload.get("sub")
    if not user_id:
        return None

    # Import here to avoid circular imports
    from app.models.user import User

    # Look up user in database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    # If user doesn't exist yet, create them from token data
    if user is None:
        email = payload.get("email", "")
        user_metadata = payload.get("user_metadata", {})

        user = User(
            id=user_id,
            email=email,
            display_name=user_metadata.get("full_name") or user_metadata.get("name") or email.split("@")[0],
            avatar_url=user_metadata.get("avatar_url"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user or raise 401."""
    user = await get_current_user_optional(credentials, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user
