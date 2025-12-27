import warnings
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import Union


class Settings(BaseSettings):
    """Application settings."""

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Development
    DEV_MODE: bool = True  # Set to False in production via environment variable

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
    DRAFT_EXPIRE_HOURS: int = 24  # Pending drafts expire after 24 hours
    MAX_PENDING_ANONYMOUS_DRAFTS: int = 3  # Max pending non-league drafts per user

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

    @model_validator(mode="after")
    def validate_production_settings(self):
        """Validate that production-critical settings are properly configured."""
        # Warn about insecure SECRET_KEY in non-dev mode
        if not self.DEV_MODE and self.SECRET_KEY == "change-me-in-production":
            raise ValueError(
                "SECRET_KEY must be changed from default value in production. "
                "Set the SECRET_KEY environment variable to a secure random value."
            )

        # Warn about missing Supabase config in non-dev mode
        if not self.DEV_MODE and not self.SUPABASE_JWT_SECRET:
            warnings.warn(
                "SUPABASE_JWT_SECRET is not set. Authentication will not work in production.",
                UserWarning,
            )

        return self

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
