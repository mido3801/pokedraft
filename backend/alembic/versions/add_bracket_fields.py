"""Add bracket fields to matches table

Revision ID: add_bracket_fields
Revises: add_pokemon_data_tables
Create Date: 2025-12-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_bracket_fields'
down_revision: Union[str, None] = 'add_pokemon_data_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add bracket-specific columns to matches table
    op.add_column('matches', sa.Column('schedule_format', sa.String(50), nullable=True))
    op.add_column('matches', sa.Column('bracket_round', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('bracket_position', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('next_match_id', sa.UUID(), nullable=True))
    op.add_column('matches', sa.Column('loser_next_match_id', sa.UUID(), nullable=True))
    op.add_column('matches', sa.Column('seed_a', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('seed_b', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('is_bye', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('matches', sa.Column('is_bracket_reset', sa.Boolean(), server_default='false', nullable=False))

    # Make team_a_id and team_b_id nullable for bracket matches (teams TBD)
    op.alter_column('matches', 'team_a_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('matches', 'team_b_id', existing_type=sa.UUID(), nullable=True)

    # Foreign key constraints for self-referential match links
    op.create_foreign_key(
        'fk_match_next_match',
        'matches', 'matches',
        ['next_match_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_match_loser_next_match',
        'matches', 'matches',
        ['loser_next_match_id'], ['id'],
        ondelete='SET NULL'
    )

    # Index for efficient bracket queries
    op.create_index(
        'ix_matches_bracket',
        'matches',
        ['season_id', 'schedule_format', 'bracket_round']
    )


def downgrade() -> None:
    op.drop_index('ix_matches_bracket', table_name='matches')
    op.drop_constraint('fk_match_loser_next_match', 'matches', type_='foreignkey')
    op.drop_constraint('fk_match_next_match', 'matches', type_='foreignkey')
    op.alter_column('matches', 'team_b_id', existing_type=sa.UUID(), nullable=False)
    op.alter_column('matches', 'team_a_id', existing_type=sa.UUID(), nullable=False)
    op.drop_column('matches', 'is_bracket_reset')
    op.drop_column('matches', 'is_bye')
    op.drop_column('matches', 'seed_b')
    op.drop_column('matches', 'seed_a')
    op.drop_column('matches', 'loser_next_match_id')
    op.drop_column('matches', 'next_match_id')
    op.drop_column('matches', 'bracket_position')
    op.drop_column('matches', 'bracket_round')
    op.drop_column('matches', 'schedule_format')
