from typing import List
from app.services.pokeapi import pokeapi_service


class TeamExportService:
    """
    Service for exporting teams in various formats.
    """

    @staticmethod
    async def to_showdown(team_name: str, pokemon_ids: List[int]) -> str:
        """
        Export team in Pokemon Showdown paste format.

        Format:
        Pokemon Name
        Ability: [ability]

        (Empty moveset - user fills in on Showdown)
        """
        lines = []

        for pokemon_id in pokemon_ids:
            pokemon = await pokeapi_service.get_pokemon(pokemon_id)
            if pokemon:
                # Pokemon name (capitalized)
                name = pokemon["name"].replace("-", " ").title()
                lines.append(name)

                # Primary ability
                if pokemon["abilities"]:
                    ability = pokemon["abilities"][0].replace("-", " ").title()
                    lines.append(f"Ability: {ability}")

                lines.append("")  # Empty line between Pokemon

        return "\n".join(lines)

    @staticmethod
    async def to_json(team_name: str, pokemon_ids: List[int]) -> dict:
        """Export team as JSON with full Pokemon data."""
        pokemon_list = []

        for pokemon_id in pokemon_ids:
            pokemon = await pokeapi_service.get_pokemon(pokemon_id)
            if pokemon:
                pokemon_list.append(pokemon)

        return {
            "team_name": team_name,
            "pokemon": pokemon_list,
        }

    @staticmethod
    async def to_csv(team_name: str, pokemon_ids: List[int]) -> str:
        """Export team as CSV."""
        lines = ["id,name,types,hp,attack,defense,sp_attack,sp_defense,speed"]

        for pokemon_id in pokemon_ids:
            pokemon = await pokeapi_service.get_pokemon(pokemon_id)
            if pokemon:
                stats = pokemon["stats"]
                types = "/".join(pokemon["types"])
                lines.append(
                    f"{pokemon['id']},"
                    f"{pokemon['name']},"
                    f"{types},"
                    f"{stats.get('hp', 0)},"
                    f"{stats.get('attack', 0)},"
                    f"{stats.get('defense', 0)},"
                    f"{stats.get('special-attack', 0)},"
                    f"{stats.get('special-defense', 0)},"
                    f"{stats.get('speed', 0)}"
                )

        return "\n".join(lines)


team_export_service = TeamExportService()
