from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Union


class Settings(BaseSettings):
    """Application settings."""

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Development
    DEV_MODE: bool = True  # Set to False in production

    # CORS - accepts comma-separated string or list
    CORS_ORIGINS: Union[list[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database (Supabase)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    DATABASE_URL: str = ""

    # Discord
    DISCORD_BOT_TOKEN: str = ""
    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""

    # OAuth (via Supabase)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Session
    SECRET_KEY: str = "change-me-in-production"
    SESSION_EXPIRE_DAYS: int = 7

    # Draft settings
    DEFAULT_TIMER_SECONDS: int = 90
    ANONYMOUS_SESSION_EXPIRE_DAYS: int = 7

    # Sprite settings (using PokeAPI CDN)
    SPRITE_BASE_URL: str = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"
    DEFAULT_SPRITE_STYLE: str = "official-artwork"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def async_database_url(self) -> str:
        """Get async database URL for SQLAlchemy async engine."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Get sync database URL for Alembic migrations."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if "+asyncpg" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
