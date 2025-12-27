"""Add unique constraint on league_memberships

Revision ID: add_membership_uq
Revises: add_auction_columns
Create Date: 2025-12-26

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'add_membership_uq'
down_revision: Union[str, None] = 'add_auction_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_league_membership',
        'league_memberships',
        ['league_id', 'user_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_league_membership', 'league_memberships', type_='unique')
