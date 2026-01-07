import secrets
from typing import Optional
import jwt
from jwt import PyJWTError, PyJWKClient

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

security = HTTPBearer(auto_error=False)

# JWKS client for Supabase token verification (ES256)
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> Optional[PyJWKClient]:
    """Get or create the JWKS client for Supabase."""
    global _jwks_client
    if _jwks_client is None and settings.SUPABASE_URL:
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        print(f"[AUTH] Initialized JWKS client: {jwks_url}")
    return _jwks_client


def generate_session_token() -> str:
    """Generate a secure session token for anonymous users."""
    return secrets.token_urlsafe(32)


def generate_rejoin_code() -> str:
    """Generate a memorable rejoin code (e.g., PIKA-7842)."""
    pokemon_prefixes = [
        "PIKA", "CHAR", "BULB", "SQRT", "EEVEE",
        "JIGG", "MEOW", "PSYD", "SLWP", "GENR",
        "UMBR", "FLAR", "JOLT", "SPND", "TTAR"
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
        # Get the algorithm from the token header
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        print(f"[AUTH DEBUG] Token algorithm: {alg}")

        # ES256 tokens require JWKS verification (Supabase default)
        if alg == "ES256":
            jwks_client = get_jwks_client()
            if jwks_client:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["ES256"],
                    audience="authenticated",
                )
                return payload
            else:
                print("[AUTH DEBUG] No JWKS client available for ES256 token")
                return None

        # HS256 tokens - try multiple keys
        # In dev mode, try SECRET_KEY first (for dev-login tokens)
        if settings.DEV_MODE:
            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"],
                    audience="authenticated",
                )
                return payload
            except PyJWTError:
                pass  # Try other methods

        # Try Supabase JWT secret
        if settings.SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    audience="authenticated",
                )
                return payload
            except PyJWTError:
                pass  # Fall through to error handling

        # No valid decode method worked
        if not settings.DEV_MODE:
            print(f"[AUTH DEBUG] No SUPABASE_JWT_SECRET configured and DEV_MODE is False")
        return None
    except PyJWTError as e:
        print(f"[AUTH DEBUG] JWT decode error: {type(e).__name__}: {e}")
        # Try to decode without verification to see the token contents for debugging
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            print(f"[AUTH DEBUG] Unverified token payload: aud={unverified.get('aud')}, sub={unverified.get('sub')}")
        except Exception:
            pass
        return None
    except Exception as e:
        # Catch network errors from JWKS client, etc.
        print(f"[AUTH DEBUG] Unexpected error: {type(e).__name__}: {e}")
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
