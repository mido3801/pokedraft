"""Sprite URL generation service."""

from enum import Enum

from app.core.config import settings


class SpriteStyle(str, Enum):
    """Available sprite styles."""

    DEFAULT = "default"
    OFFICIAL_ARTWORK = "official-artwork"
    HOME = "home"
    SHINY = "shiny"
    SHINY_OFFICIAL = "shiny-official-artwork"
    SHINY_HOME = "shiny-home"


# Mapping of styles to directory paths relative to sprite base
SPRITE_PATHS = {
    SpriteStyle.DEFAULT: "",
    SpriteStyle.OFFICIAL_ARTWORK: "other/official-artwork",
    SpriteStyle.HOME: "other/home",
    SpriteStyle.SHINY: "shiny",
    SpriteStyle.SHINY_OFFICIAL: "other/official-artwork/shiny",
    SpriteStyle.SHINY_HOME: "other/home/shiny",
}


def get_sprite_url(
    pokemon_id: int,
    style: SpriteStyle | str | None = None,
    shiny: bool = False,
) -> str:
    """
    Generate sprite URL for a Pokemon.

    Args:
        pokemon_id: The Pokemon's PokeAPI ID
        style: The sprite style (default, official-artwork, home)
        shiny: Whether to return shiny variant

    Returns:
        URL path to the sprite image
    """
    # Handle string style
    if isinstance(style, str):
        try:
            style = SpriteStyle(style)
        except ValueError:
            style = None

    # Use default style from settings if not specified
    if style is None:
        try:
            style = SpriteStyle(settings.DEFAULT_SPRITE_STYLE)
        except ValueError:
            style = SpriteStyle.OFFICIAL_ARTWORK

    # Handle shiny override
    if shiny:
        if style == SpriteStyle.DEFAULT:
            style = SpriteStyle.SHINY
        elif style == SpriteStyle.OFFICIAL_ARTWORK:
            style = SpriteStyle.SHINY_OFFICIAL
        elif style == SpriteStyle.HOME:
            style = SpriteStyle.SHINY_HOME

    # Build URL path
    base = settings.SPRITE_BASE_URL
    subpath = SPRITE_PATHS.get(style, "")

    if subpath:
        return f"{base}/{subpath}/{pokemon_id}.png"
    else:
        return f"{base}/{pokemon_id}.png"


def get_all_sprite_urls(pokemon_id: int) -> dict[str, str]:
    """
    Get all available sprite URLs for a Pokemon.

    Returns a dictionary with style names as keys and URLs as values.
    """
    return {
        "default": get_sprite_url(pokemon_id, SpriteStyle.DEFAULT),
        "official-artwork": get_sprite_url(pokemon_id, SpriteStyle.OFFICIAL_ARTWORK),
        "home": get_sprite_url(pokemon_id, SpriteStyle.HOME),
        "shiny": get_sprite_url(pokemon_id, SpriteStyle.SHINY),
        "shiny-official-artwork": get_sprite_url(pokemon_id, SpriteStyle.SHINY_OFFICIAL),
        "shiny-home": get_sprite_url(pokemon_id, SpriteStyle.SHINY_HOME),
    }
