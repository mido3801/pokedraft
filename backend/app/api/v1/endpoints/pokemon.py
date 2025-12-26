"""Pokemon API endpoints."""

from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.pokeapi import pokeapi_service
from app.services.sprites import SpriteStyle, get_all_sprite_urls
from app.schemas.pokemon import (
    Pokemon,
    PokemonList,
    PokemonBoxResponse,
    PokemonSummary,
    PokemonTypeResponse,
    SpriteUrls,
)

router = APIRouter()


@router.get("", response_model=PokemonList)
async def search_pokemon(
    query: Optional[str] = Query(None, description="Search term for Pokemon name"),
    type: Optional[str] = Query(None, description="Filter by type (e.g., fire, water)"),
    generation: Optional[int] = Query(None, ge=1, le=9, description="Filter by generation (1-9)"),
    is_legendary: Optional[bool] = Query(None, description="Filter for legendary Pokemon"),
    is_mythical: Optional[bool] = Query(None, description="Filter for mythical Pokemon"),
    sprite_style: Optional[SpriteStyle] = Query(None, description="Sprite style to use"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search and filter Pokemon.

    Returns a paginated list of Pokemon matching the specified filters.
    """
    pokemon = await pokeapi_service.search_pokemon(
        db=db,
        query=query,
        type_filter=type,
        generation=generation,
        is_legendary=is_legendary,
        is_mythical=is_mythical,
        limit=limit,
        offset=offset,
        sprite_style=sprite_style,
    )

    total = await pokeapi_service.get_pokemon_count(db)

    return PokemonList(
        pokemon=pokemon,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/box", response_model=PokemonBoxResponse)
async def get_all_pokemon_for_box(
    sprite_style: Optional[SpriteStyle] = Query(SpriteStyle.DEFAULT, description="Sprite style to use"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all Pokemon with metadata for the box display.

    Returns all Pokemon with: id, name, sprite, types, generation, bst,
    evolution_stage, is_legendary, is_mythical.

    Optimized for rendering the Pokemon selection box on draft creation.
    """
    pokemon = await pokeapi_service.get_all_pokemon_for_box(db, sprite_style)
    return PokemonBoxResponse(pokemon=pokemon, total=len(pokemon))


@router.get("/types", response_model=List[PokemonTypeResponse])
async def get_types(
    db: AsyncSession = Depends(get_db),
):
    """Get all Pokemon types."""
    return await pokeapi_service.get_types(db)


@router.get("/generation/{generation}", response_model=List[PokemonSummary])
async def get_generation_pokemon(
    generation: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all Pokemon from a specific generation."""
    if generation < 1 or generation > 9:
        raise HTTPException(status_code=400, detail="Generation must be between 1 and 9")

    return await pokeapi_service.get_generation_pokemon(generation, db)


@router.get("/{pokemon_id}", response_model=Pokemon)
async def get_pokemon_by_id(
    pokemon_id: int,
    sprite_style: Optional[SpriteStyle] = Query(None, description="Sprite style to use"),
    db: AsyncSession = Depends(get_db),
):
    """Get Pokemon by ID."""
    pokemon = await pokeapi_service.get_pokemon(pokemon_id, db, sprite_style)

    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokemon not found")

    return pokemon


@router.get("/{pokemon_id}/sprites", response_model=SpriteUrls)
async def get_pokemon_sprites(
    pokemon_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all available sprite URLs for a Pokemon."""
    # Verify Pokemon exists
    pokemon = await pokeapi_service.get_pokemon(pokemon_id, db)
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokemon not found")

    return get_all_sprite_urls(pokemon_id)


@router.get("/name/{name}", response_model=Pokemon)
async def get_pokemon_by_name(
    name: str,
    sprite_style: Optional[SpriteStyle] = Query(None, description="Sprite style to use"),
    db: AsyncSession = Depends(get_db),
):
    """Get Pokemon by name."""
    pokemon = await pokeapi_service.get_pokemon_by_name(name, db, sprite_style)

    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokemon not found")

    return pokemon
