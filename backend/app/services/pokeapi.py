import httpx
from typing import Optional, Dict, List
from functools import lru_cache


POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"


class PokeAPIService:
    """
    Service for fetching Pokemon data from PokeAPI.

    Implements caching to reduce API calls.
    """

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        self._cache: Dict[str, dict] = {}

    async def get_pokemon(self, pokemon_id: int) -> Optional[dict]:
        """Get Pokemon data by ID."""
        cache_key = f"pokemon:{pokemon_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            response = await self._client.get(f"{POKEAPI_BASE_URL}/pokemon/{pokemon_id}")
            response.raise_for_status()
            data = response.json()

            pokemon = {
                "id": data["id"],
                "name": data["name"],
                "types": [t["type"]["name"] for t in data["types"]],
                "sprite": data["sprites"]["front_default"],
                "stats": {
                    stat["stat"]["name"]: stat["base_stat"]
                    for stat in data["stats"]
                },
                "abilities": [a["ability"]["name"] for a in data["abilities"]],
            }

            self._cache[cache_key] = pokemon
            return pokemon
        except httpx.HTTPError:
            return None

    async def get_pokemon_by_name(self, name: str) -> Optional[dict]:
        """Get Pokemon data by name."""
        cache_key = f"pokemon:name:{name.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            response = await self._client.get(f"{POKEAPI_BASE_URL}/pokemon/{name.lower()}")
            response.raise_for_status()
            data = response.json()

            pokemon = {
                "id": data["id"],
                "name": data["name"],
                "types": [t["type"]["name"] for t in data["types"]],
                "sprite": data["sprites"]["front_default"],
                "stats": {
                    stat["stat"]["name"]: stat["base_stat"]
                    for stat in data["stats"]
                },
                "abilities": [a["ability"]["name"] for a in data["abilities"]],
            }

            self._cache[cache_key] = pokemon
            self._cache[f"pokemon:{data['id']}"] = pokemon
            return pokemon
        except httpx.HTTPError:
            return None

    async def get_generation_pokemon(self, generation: int) -> List[dict]:
        """Get all Pokemon from a specific generation."""
        try:
            response = await self._client.get(f"{POKEAPI_BASE_URL}/generation/{generation}")
            response.raise_for_status()
            data = response.json()

            pokemon_list = []
            for species in data["pokemon_species"]:
                # Extract ID from URL
                pokemon_id = int(species["url"].split("/")[-2])
                pokemon_list.append({
                    "id": pokemon_id,
                    "name": species["name"],
                })

            return sorted(pokemon_list, key=lambda x: x["id"])
        except httpx.HTTPError:
            return []

    async def validate_pokemon_ids(self, pokemon_ids: List[int]) -> Dict[int, bool]:
        """Validate that a list of Pokemon IDs are valid."""
        results = {}
        for pokemon_id in pokemon_ids:
            pokemon = await self.get_pokemon(pokemon_id)
            results[pokemon_id] = pokemon is not None
        return results

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# Singleton instance
pokeapi_service = PokeAPIService()
