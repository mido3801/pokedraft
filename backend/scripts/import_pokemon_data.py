#!/usr/bin/env python3
"""
Import Pokemon data from PokeAPI CSV files into PostgreSQL.

Usage:
    python scripts/import_pokemon_data.py [--csv-path PATH]

The CSV path defaults to /app/pokeapi_data/csv when running in Docker,
or ../pokeapi/data/v2/csv when running locally.
"""

import argparse
import csv
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import get_sync_database_url


def get_csv_path() -> Path:
    """Determine the CSV data path based on environment."""
    # Docker path
    docker_path = Path("/app/pokeapi_data/csv")
    if docker_path.exists():
        return docker_path

    # Local development path
    local_path = Path(__file__).parent.parent.parent / "pokeapi" / "data" / "v2" / "csv"
    if local_path.exists():
        return local_path

    raise FileNotFoundError("Could not find PokeAPI CSV data directory")


def read_csv(csv_path: Path, filename: str) -> list[dict]:
    """Read a CSV file and return list of dictionaries."""
    filepath = csv_path / filename
    print(f"  Reading {filename}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def parse_bool(value: str) -> bool:
    """Parse boolean from CSV string."""
    return value == '1' or value.lower() == 'true'


def parse_int_or_none(value: str) -> int | None:
    """Parse integer, returning None for empty strings."""
    if value == '' or value is None:
        return None
    return int(value)


def import_types(session, csv_path: Path) -> None:
    """Import Pokemon types."""
    print("\nImporting Pokemon types...")
    rows = read_csv(csv_path, "types.csv")

    for row in rows:
        session.execute(
            text("""
                INSERT INTO pokemon_types_ref (id, identifier, generation_id)
                VALUES (:id, :identifier, :generation_id)
                ON CONFLICT (id) DO UPDATE SET
                    identifier = EXCLUDED.identifier,
                    generation_id = EXCLUDED.generation_id
            """),
            {
                "id": int(row["id"]),
                "identifier": row["identifier"],
                "generation_id": int(row["generation_id"]),
            }
        )

    session.commit()
    print(f"  Imported {len(rows)} types")


def import_stats(session, csv_path: Path) -> None:
    """Import Pokemon stats."""
    print("\nImporting Pokemon stats...")
    rows = read_csv(csv_path, "stats.csv")

    # Only import the 6 main battle stats
    main_stats = [r for r in rows if r["is_battle_only"] == "0" and int(r["id"]) <= 6]

    for row in main_stats:
        session.execute(
            text("""
                INSERT INTO pokemon_stats_ref (id, identifier)
                VALUES (:id, :identifier)
                ON CONFLICT (id) DO UPDATE SET identifier = EXCLUDED.identifier
            """),
            {
                "id": int(row["id"]),
                "identifier": row["identifier"],
            }
        )

    session.commit()
    print(f"  Imported {len(main_stats)} stats")


def import_abilities(session, csv_path: Path) -> None:
    """Import Pokemon abilities."""
    print("\nImporting Pokemon abilities...")
    rows = read_csv(csv_path, "abilities.csv")

    for row in rows:
        session.execute(
            text("""
                INSERT INTO pokemon_abilities_ref (id, identifier, generation_id, is_main_series)
                VALUES (:id, :identifier, :generation_id, :is_main_series)
                ON CONFLICT (id) DO UPDATE SET
                    identifier = EXCLUDED.identifier,
                    generation_id = EXCLUDED.generation_id,
                    is_main_series = EXCLUDED.is_main_series
            """),
            {
                "id": int(row["id"]),
                "identifier": row["identifier"],
                "generation_id": int(row["generation_id"]),
                "is_main_series": parse_bool(row["is_main_series"]),
            }
        )

    session.commit()
    print(f"  Imported {len(rows)} abilities")


def import_species(session, csv_path: Path) -> None:
    """Import Pokemon species."""
    print("\nImporting Pokemon species...")
    rows = read_csv(csv_path, "pokemon_species.csv")

    # First pass: insert all species without evolves_from (to avoid FK issues)
    for row in rows:
        session.execute(
            text("""
                INSERT INTO pokemon_species (id, identifier, generation_id, evolves_from_species_id, is_legendary, is_mythical)
                VALUES (:id, :identifier, :generation_id, NULL, :is_legendary, :is_mythical)
                ON CONFLICT (id) DO UPDATE SET
                    identifier = EXCLUDED.identifier,
                    generation_id = EXCLUDED.generation_id,
                    is_legendary = EXCLUDED.is_legendary,
                    is_mythical = EXCLUDED.is_mythical
            """),
            {
                "id": int(row["id"]),
                "identifier": row["identifier"],
                "generation_id": int(row["generation_id"]),
                "is_legendary": parse_bool(row["is_legendary"]),
                "is_mythical": parse_bool(row["is_mythical"]),
            }
        )

    session.commit()

    # Second pass: update evolves_from_species_id
    for row in rows:
        evolves_from = parse_int_or_none(row["evolves_from_species_id"])
        if evolves_from:
            session.execute(
                text("""
                    UPDATE pokemon_species
                    SET evolves_from_species_id = :evolves_from
                    WHERE id = :id
                """),
                {
                    "id": int(row["id"]),
                    "evolves_from": evolves_from,
                }
            )

    session.commit()
    print(f"  Imported {len(rows)} species")


def import_pokemon(session, csv_path: Path) -> None:
    """Import Pokemon (main forms only by default)."""
    print("\nImporting Pokemon...")
    rows = read_csv(csv_path, "pokemon.csv")

    # Filter to default forms only (is_default = 1)
    default_forms = [r for r in rows if parse_bool(r["is_default"])]

    for row in default_forms:
        session.execute(
            text("""
                INSERT INTO pokemon_data (id, identifier, species_id, height, weight, base_experience, is_default)
                VALUES (:id, :identifier, :species_id, :height, :weight, :base_experience, :is_default)
                ON CONFLICT (id) DO UPDATE SET
                    identifier = EXCLUDED.identifier,
                    species_id = EXCLUDED.species_id,
                    height = EXCLUDED.height,
                    weight = EXCLUDED.weight,
                    base_experience = EXCLUDED.base_experience,
                    is_default = EXCLUDED.is_default
            """),
            {
                "id": int(row["id"]),
                "identifier": row["identifier"],
                "species_id": int(row["species_id"]),
                "height": int(row["height"]),
                "weight": int(row["weight"]),
                "base_experience": parse_int_or_none(row["base_experience"]),
                "is_default": True,
            }
        )

    session.commit()
    print(f"  Imported {len(default_forms)} Pokemon (default forms)")


def import_pokemon_types(session, csv_path: Path) -> None:
    """Import Pokemon type associations."""
    print("\nImporting Pokemon type links...")
    rows = read_csv(csv_path, "pokemon_types.csv")

    # Get valid pokemon IDs from our pokemon_data table
    result = session.execute(text("SELECT id FROM pokemon_data"))
    valid_pokemon_ids = {row[0] for row in result}

    count = 0
    for row in rows:
        pokemon_id = int(row["pokemon_id"])
        if pokemon_id not in valid_pokemon_ids:
            continue

        session.execute(
            text("""
                INSERT INTO pokemon_type_links (pokemon_id, type_id, slot)
                VALUES (:pokemon_id, :type_id, :slot)
                ON CONFLICT (pokemon_id, type_id) DO UPDATE SET slot = EXCLUDED.slot
            """),
            {
                "pokemon_id": pokemon_id,
                "type_id": int(row["type_id"]),
                "slot": int(row["slot"]),
            }
        )
        count += 1

    session.commit()
    print(f"  Imported {count} type links")


def import_pokemon_stats(session, csv_path: Path) -> None:
    """Import Pokemon base stats."""
    print("\nImporting Pokemon stat values...")
    rows = read_csv(csv_path, "pokemon_stats.csv")

    # Get valid pokemon IDs
    result = session.execute(text("SELECT id FROM pokemon_data"))
    valid_pokemon_ids = {row[0] for row in result}

    count = 0
    for row in rows:
        pokemon_id = int(row["pokemon_id"])
        stat_id = int(row["stat_id"])

        # Only import main stats (1-6) for valid pokemon
        if pokemon_id not in valid_pokemon_ids or stat_id > 6:
            continue

        session.execute(
            text("""
                INSERT INTO pokemon_stat_values (pokemon_id, stat_id, base_stat)
                VALUES (:pokemon_id, :stat_id, :base_stat)
                ON CONFLICT (pokemon_id, stat_id) DO UPDATE SET base_stat = EXCLUDED.base_stat
            """),
            {
                "pokemon_id": pokemon_id,
                "stat_id": stat_id,
                "base_stat": int(row["base_stat"]),
            }
        )
        count += 1

    session.commit()
    print(f"  Imported {count} stat values")


def import_pokemon_abilities(session, csv_path: Path) -> None:
    """Import Pokemon ability associations."""
    print("\nImporting Pokemon ability links...")
    rows = read_csv(csv_path, "pokemon_abilities.csv")

    # Get valid pokemon IDs
    result = session.execute(text("SELECT id FROM pokemon_data"))
    valid_pokemon_ids = {row[0] for row in result}

    count = 0
    for row in rows:
        pokemon_id = int(row["pokemon_id"])
        if pokemon_id not in valid_pokemon_ids:
            continue

        session.execute(
            text("""
                INSERT INTO pokemon_ability_links (pokemon_id, ability_id, is_hidden, slot)
                VALUES (:pokemon_id, :ability_id, :is_hidden, :slot)
                ON CONFLICT (pokemon_id, ability_id) DO UPDATE SET
                    is_hidden = EXCLUDED.is_hidden,
                    slot = EXCLUDED.slot
            """),
            {
                "pokemon_id": pokemon_id,
                "ability_id": int(row["ability_id"]),
                "is_hidden": parse_bool(row["is_hidden"]),
                "slot": int(row["slot"]),
            }
        )
        count += 1

    session.commit()
    print(f"  Imported {count} ability links")


def main():
    parser = argparse.ArgumentParser(description="Import Pokemon data from CSV files")
    parser.add_argument(
        "--csv-path",
        type=Path,
        help="Path to CSV data directory",
    )
    args = parser.parse_args()

    # Determine CSV path
    csv_path = args.csv_path or get_csv_path()
    print(f"Using CSV data from: {csv_path}")

    # Create database connection
    database_url = get_sync_database_url()
    print(f"Connecting to database...")

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("\n" + "=" * 50)
        print("Starting Pokemon data import")
        print("=" * 50)

        # Import in dependency order
        import_types(session, csv_path)
        import_stats(session, csv_path)
        import_abilities(session, csv_path)
        import_species(session, csv_path)
        import_pokemon(session, csv_path)
        import_pokemon_types(session, csv_path)
        import_pokemon_stats(session, csv_path)
        import_pokemon_abilities(session, csv_path)

        print("\n" + "=" * 50)
        print("Import completed successfully!")
        print("=" * 50)

        # Print summary
        result = session.execute(text("SELECT COUNT(*) FROM pokemon_data"))
        pokemon_count = result.scalar()
        print(f"\nTotal Pokemon in database: {pokemon_count}")

    except Exception as e:
        session.rollback()
        print(f"\nError during import: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
