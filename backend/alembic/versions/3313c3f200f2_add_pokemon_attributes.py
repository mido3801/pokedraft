"""add_pokemon_attributes

Revision ID: 3313c3f200f2
Revises: add_pool_presets
Create Date: 2025-12-31 19:27:39.754934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3313c3f200f2'
down_revision: Union[str, None] = 'add_pool_presets'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to pokemon_data table
    op.add_column('pokemon_data', sa.Column('generation', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('pokemon_data', sa.Column('base_stat_total', sa.Integer(), nullable=False, server_default='400'))
    op.add_column('pokemon_data', sa.Column('evolution_stage', sa.String(length=50), nullable=False, server_default='unevolved'))
    op.add_column('pokemon_data', sa.Column('is_legendary', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('pokemon_data', sa.Column('is_mythical', sa.Boolean(), nullable=False, server_default='false'))

    # Create indexes for filtering
    op.create_index('ix_pokemon_data_generation', 'pokemon_data', ['generation'])
    op.create_index('ix_pokemon_data_base_stat_total', 'pokemon_data', ['base_stat_total'])
    op.create_index('ix_pokemon_data_is_legendary', 'pokemon_data', ['is_legendary'])
    op.create_index('ix_pokemon_data_is_mythical', 'pokemon_data', ['is_mythical'])

    # Remove server defaults after adding columns (so new inserts don't use defaults)
    op.alter_column('pokemon_data', 'generation', server_default=None)
    op.alter_column('pokemon_data', 'base_stat_total', server_default=None)
    op.alter_column('pokemon_data', 'evolution_stage', server_default=None)
    op.alter_column('pokemon_data', 'is_legendary', server_default=None)
    op.alter_column('pokemon_data', 'is_mythical', server_default=None)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_pokemon_data_is_mythical', table_name='pokemon_data')
    op.drop_index('ix_pokemon_data_is_legendary', table_name='pokemon_data')
    op.drop_index('ix_pokemon_data_base_stat_total', table_name='pokemon_data')
    op.drop_index('ix_pokemon_data_generation', table_name='pokemon_data')

    # Drop columns
    op.drop_column('pokemon_data', 'is_mythical')
    op.drop_column('pokemon_data', 'is_legendary')
    op.drop_column('pokemon_data', 'evolution_stage')
    op.drop_column('pokemon_data', 'base_stat_total')
    op.drop_column('pokemon_data', 'generation')
