"""Add creator_id column to drafts table

Revision ID: add_draft_creator_id
Revises: add_membership_uq
Create Date: 2025-12-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_draft_creator_id'
down_revision: Union[str, None] = 'add_membership_uq'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('drafts', sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_drafts_creator_id',
        'drafts',
        'users',
        ['creator_id'],
        ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_drafts_creator_id', 'drafts', type_='foreignkey')
    op.drop_column('drafts', 'creator_id')
