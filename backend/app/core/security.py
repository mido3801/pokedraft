import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

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


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None
    # TODO: Validate token with Supabase Auth
    return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Get current authenticated user or raise 401."""
    user = await get_current_user_optional(credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user
