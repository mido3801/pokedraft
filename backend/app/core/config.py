from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database (Supabase)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
