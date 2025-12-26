"""Pokemon API schemas."""

from typing import Optional, List, Dict

from pydantic import BaseModel, Field

from app.services.sprites import SpriteStyle


class PokemonBase(BaseModel):
    """Base Pokemon data."""

    id: int
    name: str
    types: List[str]
    sprite: str


class Pokemon(PokemonBase):
    """Full Pokemon data."""

    stats: Dict[str, int]
    bst: Optional[int] = None
    abilities: List[str]
    generation: Optional[int] = None
    is_legendary: bool = False
    is_mythical: bool = False
    evolution_stage: Optional[int] = None  # 0=unevolved, 1=middle, 2=fully evolved


class PokemonBoxEntry(BaseModel):
    """Pokemon data optimized for box display."""

    id: int
    name: str
    sprite: str
    types: List[str]
    generation: Optional[int] = None
    bst: int
    evolution_stage: int  # 0=unevolved, 1=middle, 2=fully evolved
    is_legendary: bool = False
    is_mythical: bool = False


class PokemonBoxResponse(BaseModel):
    """Response containing all Pokemon for box display."""

    pokemon: List[PokemonBoxEntry]
    total: int


class PokemonSummary(BaseModel):
    """Lightweight Pokemon summary for lists."""

    id: int
    name: str


class PokemonList(BaseModel):
    """Paginated list of Pokemon."""

    pokemon: List[Pokemon]
    total: int
    limit: int
    offset: int


class PokemonTypeResponse(BaseModel):
    """Pokemon type data."""

    id: int
    name: str


class SpriteUrls(BaseModel):
    """All available sprite URLs for a Pokemon."""

    default: str
    official_artwork: str = Field(alias="official-artwork")
    home: str
    shiny: str
    shiny_official_artwork: str = Field(alias="shiny-official-artwork")
    shiny_home: str = Field(alias="shiny-home")

    class Config:
        populate_by_name = True
