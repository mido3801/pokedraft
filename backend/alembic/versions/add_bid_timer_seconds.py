"""Add bid_timer_seconds column for auction drafts

Revision ID: add_bid_timer_seconds
Revises: add_discord_tables
Create Date: 2026-01-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_bid_timer_seconds'
down_revision: Union[str, None] = 'add_discord_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('drafts', sa.Column('bid_timer_seconds', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('drafts', 'bid_timer_seconds')
