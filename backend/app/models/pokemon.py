"""Pokemon data models - stores PokeAPI data locally."""

from sqlalchemy import String, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PokemonType(Base):
    """Pokemon type reference table (fire, water, etc.)."""

    __tablename__ = "pokemon_types_ref"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    generation_id: Mapped[int] = mapped_column(Integer)

    pokemon_links = relationship("PokemonTypeLink", back_populates="type")


class PokemonStat(Base):
    """Pokemon stat reference table (hp, attack, etc.)."""

    __tablename__ = "pokemon_stats_ref"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(50), unique=True)

    pokemon_values = relationship("PokemonStatValue", back_populates="stat")


class PokemonAbility(Base):
    """Pokemon ability reference table."""

    __tablename__ = "pokemon_abilities_ref"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(100), index=True)
    generation_id: Mapped[int] = mapped_column(Integer)
    is_main_series: Mapped[bool] = mapped_column(Boolean, default=True)

    pokemon_links = relationship("PokemonAbilityLink", back_populates="ability")


class PokemonSpecies(Base):
    """Pokemon species with generation and evolution info."""

    __tablename__ = "pokemon_species"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    generation_id: Mapped[int] = mapped_column(Integer, index=True)
    evolves_from_species_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pokemon_species.id"), nullable=True
    )
    is_legendary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_mythical: Mapped[bool] = mapped_column(Boolean, default=False)

    pokemon = relationship("Pokemon", back_populates="species")
    evolves_from = relationship("PokemonSpecies", remote_side=[id])


class Pokemon(Base):
    """Main Pokemon table."""

    __tablename__ = "pokemon_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(100), index=True)
    species_id: Mapped[int] = mapped_column(Integer, ForeignKey("pokemon_species.id"))
    height: Mapped[int] = mapped_column(Integer)
    weight: Mapped[int] = mapped_column(Integer)
    base_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)
    generation: Mapped[int] = mapped_column(Integer, index=True)
    base_stat_total: Mapped[int] = mapped_column(Integer, index=True)
    evolution_stage: Mapped[str] = mapped_column(String(50))
    is_legendary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_mythical: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    species = relationship("PokemonSpecies", back_populates="pokemon")
    types = relationship("PokemonTypeLink", back_populates="pokemon", lazy="selectin")
    stats = relationship("PokemonStatValue", back_populates="pokemon", lazy="selectin")
    abilities = relationship("PokemonAbilityLink", back_populates="pokemon", lazy="selectin")

    @property
    def name(self) -> str:
        """Return the Pokemon's name (formatted identifier)."""
        return self.identifier.title() if self.identifier else ""


class PokemonTypeLink(Base):
    """Many-to-many: Pokemon <-> Types."""

    __tablename__ = "pokemon_type_links"

    pokemon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pokemon_data.id"), primary_key=True
    )
    type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pokemon_types_ref.id"), primary_key=True
    )
    slot: Mapped[int] = mapped_column(Integer)  # 1 = primary, 2 = secondary

    pokemon = relationship("Pokemon", back_populates="types")
    type = relationship("PokemonType", back_populates="pokemon_links")


class PokemonStatValue(Base):
    """Pokemon base stat values."""

    __tablename__ = "pokemon_stat_values"

    pokemon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pokemon_data.id"), primary_key=True
    )
    stat_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pokemon_stats_ref.id"), primary_key=True
    )
    base_stat: Mapped[int] = mapped_column(Integer)

    pokemon = relationship("Pokemon", back_populates="stats")
    stat = relationship("PokemonStat", back_populates="pokemon_values")


class PokemonAbilityLink(Base):
    """Many-to-many: Pokemon <-> Abilities."""

    __tablename__ = "pokemon_ability_links"

    pokemon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pokemon_data.id"), primary_key=True
    )
    ability_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pokemon_abilities_ref.id"), primary_key=True
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    slot: Mapped[int] = mapped_column(Integer)

    pokemon = relationship("Pokemon", back_populates="abilities")
    ability = relationship("PokemonAbility", back_populates="pokemon_links")
