"""Add waiver_claims and waiver_votes tables

Revision ID: add_waiver_claims
Revises: 3313c3f200f2
Create Date: 2025-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_waiver_claims'
down_revision: Union[str, None] = '3313c3f200f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create waiver_claim_status enum
    waiver_claim_status = postgresql.ENUM(
        'pending', 'approved', 'rejected', 'cancelled', 'expired',
        name='waiverclaimstatus',
        create_type=False
    )
    waiver_claim_status.create(op.get_bind(), checkfirst=True)

    # Create waiver_processing_type enum
    waiver_processing_type = postgresql.ENUM(
        'immediate', 'next_week',
        name='waiverprocessingtype',
        create_type=False
    )
    waiver_processing_type.create(op.get_bind(), checkfirst=True)

    # Create waiver_claims table
    op.create_table(
        'waiver_claims',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('season_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seasons.id'), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('pokemon_id', sa.Integer, nullable=False),
        sa.Column('drop_pokemon_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', 'cancelled', 'expired', name='waiverclaimstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='0'),
        sa.Column('requires_approval', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('admin_approved', sa.Boolean, nullable=True),
        sa.Column('admin_notes', sa.String(500), nullable=True),
        sa.Column('votes_for', sa.Integer, nullable=False, server_default='0'),
        sa.Column('votes_against', sa.Integer, nullable=False, server_default='0'),
        sa.Column('votes_required', sa.Integer, nullable=True),
        sa.Column('processing_type', postgresql.ENUM('immediate', 'next_week', name='waiverprocessingtype', create_type=False), nullable=False, server_default='immediate'),
        sa.Column('process_after', sa.DateTime, nullable=True),
        sa.Column('week_number', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
    )

    # Create indexes for efficient queries
    op.create_index('ix_waiver_claims_season_id', 'waiver_claims', ['season_id'])
    op.create_index('ix_waiver_claims_team_id', 'waiver_claims', ['team_id'])
    op.create_index('ix_waiver_claims_status', 'waiver_claims', ['status'])
    op.create_index('ix_waiver_claims_pokemon_id', 'waiver_claims', ['pokemon_id'])
    op.create_index('ix_waiver_claims_week_number', 'waiver_claims', ['week_number'])

    # Create waiver_votes table
    op.create_table(
        'waiver_votes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('waiver_claim_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('waiver_claims.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('vote', sa.Boolean, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for waiver_votes
    op.create_index('ix_waiver_votes_waiver_claim_id', 'waiver_votes', ['waiver_claim_id'])
    op.create_index('ix_waiver_votes_user_id', 'waiver_votes', ['user_id'])

    # Create unique constraint to prevent duplicate votes
    op.create_unique_constraint(
        'uq_waiver_votes_claim_user',
        'waiver_votes',
        ['waiver_claim_id', 'user_id']
    )


def downgrade() -> None:
    # Drop waiver_votes table
    op.drop_constraint('uq_waiver_votes_claim_user', 'waiver_votes', type_='unique')
    op.drop_index('ix_waiver_votes_user_id', table_name='waiver_votes')
    op.drop_index('ix_waiver_votes_waiver_claim_id', table_name='waiver_votes')
    op.drop_table('waiver_votes')

    # Drop waiver_claims table
    op.drop_index('ix_waiver_claims_week_number', table_name='waiver_claims')
    op.drop_index('ix_waiver_claims_pokemon_id', table_name='waiver_claims')
    op.drop_index('ix_waiver_claims_status', table_name='waiver_claims')
    op.drop_index('ix_waiver_claims_team_id', table_name='waiver_claims')
    op.drop_index('ix_waiver_claims_season_id', table_name='waiver_claims')
    op.drop_table('waiver_claims')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS waiverprocessingtype')
    op.execute('DROP TYPE IF EXISTS waiverclaimstatus')
