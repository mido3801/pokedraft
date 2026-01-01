import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PoolPreset(Base):
    """Pokemon pool preset - a saved pool configuration with optional point values."""

    __tablename__ = "pool_presets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Full pokemon pool stored as JSONB (self-contained)
    # Structure: { "pokemon_id": { "name": str, "points": int|null, "types": [...], ... } }
    pokemon_pool: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Filter settings used to generate the pool (optional - for recreating filters)
    # Structure matches PokemonFilters schema
    pokemon_filters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Pool metadata for display
    pokemon_count: Mapped[int] = mapped_column(Integer, default=0)

    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="pool_presets")
