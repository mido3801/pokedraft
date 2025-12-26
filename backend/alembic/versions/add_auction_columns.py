"""Add auction draft columns

Revision ID: add_auction_columns
Revises: add_bracket_fields
Create Date: 2025-12-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_auction_columns'
down_revision: Union[str, None] = 'add_bracket_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('drafts', sa.Column('nomination_timer_seconds', sa.Integer(), nullable=True))
    op.add_column('drafts', sa.Column('min_bid', sa.Integer(), nullable=True))
    op.add_column('drafts', sa.Column('bid_increment', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('drafts', 'bid_increment')
    op.drop_column('drafts', 'min_bid')
    op.drop_column('drafts', 'nomination_timer_seconds')
