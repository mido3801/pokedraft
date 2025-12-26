"""Add Pokemon data tables

Revision ID: add_pokemon_data_tables
Revises: 40b9e910d3d8
Create Date: 2025-12-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_pokemon_data_tables'
down_revision: Union[str, None] = '40b9e910d3d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reference tables (no foreign keys)
    op.create_table('pokemon_types_ref',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('identifier', sa.String(length=50), nullable=False),
        sa.Column('generation_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identifier')
    )
    op.create_index('ix_pokemon_types_ref_identifier', 'pokemon_types_ref', ['identifier'])

    op.create_table('pokemon_stats_ref',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('identifier', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identifier')
    )

    op.create_table('pokemon_abilities_ref',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('identifier', sa.String(length=100), nullable=False),
        sa.Column('generation_id', sa.Integer(), nullable=False),
        sa.Column('is_main_series', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pokemon_abilities_ref_identifier', 'pokemon_abilities_ref', ['identifier'])

    # Species table (self-referential FK)
    op.create_table('pokemon_species',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('identifier', sa.String(length=100), nullable=False),
        sa.Column('generation_id', sa.Integer(), nullable=False),
        sa.Column('evolves_from_species_id', sa.Integer(), nullable=True),
        sa.Column('is_legendary', sa.Boolean(), nullable=False),
        sa.Column('is_mythical', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['evolves_from_species_id'], ['pokemon_species.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identifier')
    )
    op.create_index('ix_pokemon_species_identifier', 'pokemon_species', ['identifier'])
    op.create_index('ix_pokemon_species_generation_id', 'pokemon_species', ['generation_id'])

    # Main Pokemon table
    op.create_table('pokemon_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('identifier', sa.String(length=100), nullable=False),
        sa.Column('species_id', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('base_experience', sa.Integer(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['species_id'], ['pokemon_species.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pokemon_data_identifier', 'pokemon_data', ['identifier'])

    # Join tables
    op.create_table('pokemon_type_links',
        sa.Column('pokemon_id', sa.Integer(), nullable=False),
        sa.Column('type_id', sa.Integer(), nullable=False),
        sa.Column('slot', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['pokemon_id'], ['pokemon_data.id']),
        sa.ForeignKeyConstraint(['type_id'], ['pokemon_types_ref.id']),
        sa.PrimaryKeyConstraint('pokemon_id', 'type_id')
    )

    op.create_table('pokemon_stat_values',
        sa.Column('pokemon_id', sa.Integer(), nullable=False),
        sa.Column('stat_id', sa.Integer(), nullable=False),
        sa.Column('base_stat', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['pokemon_id'], ['pokemon_data.id']),
        sa.ForeignKeyConstraint(['stat_id'], ['pokemon_stats_ref.id']),
        sa.PrimaryKeyConstraint('pokemon_id', 'stat_id')
    )

    op.create_table('pokemon_ability_links',
        sa.Column('pokemon_id', sa.Integer(), nullable=False),
        sa.Column('ability_id', sa.Integer(), nullable=False),
        sa.Column('is_hidden', sa.Boolean(), nullable=False),
        sa.Column('slot', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['pokemon_id'], ['pokemon_data.id']),
        sa.ForeignKeyConstraint(['ability_id'], ['pokemon_abilities_ref.id']),
        sa.PrimaryKeyConstraint('pokemon_id', 'ability_id')
    )


def downgrade() -> None:
    op.drop_table('pokemon_ability_links')
    op.drop_table('pokemon_stat_values')
    op.drop_table('pokemon_type_links')
    op.drop_index('ix_pokemon_data_identifier', table_name='pokemon_data')
    op.drop_table('pokemon_data')
    op.drop_index('ix_pokemon_species_generation_id', table_name='pokemon_species')
    op.drop_index('ix_pokemon_species_identifier', table_name='pokemon_species')
    op.drop_table('pokemon_species')
    op.drop_index('ix_pokemon_abilities_ref_identifier', table_name='pokemon_abilities_ref')
    op.drop_table('pokemon_abilities_ref')
    op.drop_table('pokemon_stats_ref')
    op.drop_index('ix_pokemon_types_ref_identifier', table_name='pokemon_types_ref')
    op.drop_table('pokemon_types_ref')
