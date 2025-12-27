"""Add pool_presets table

Revision ID: add_pool_presets
Revises: add_draft_creator_id
Create Date: 2025-12-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_pool_presets'
down_revision: Union[str, None] = 'add_draft_creator_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pool_presets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('pokemon_pool', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('pokemon_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    # Index for efficient queries
    op.create_index('ix_pool_presets_user_id', 'pool_presets', ['user_id'])
    op.create_index('ix_pool_presets_is_public', 'pool_presets', ['is_public'])


def downgrade() -> None:
    op.drop_index('ix_pool_presets_is_public')
    op.drop_index('ix_pool_presets_user_id')
    op.drop_table('pool_presets')
