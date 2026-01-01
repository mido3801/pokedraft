"""Add pokemon_filters column to pool_presets

Revision ID: add_preset_filters
Revises: add_waiver_claims
Create Date: 2025-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_preset_filters'
down_revision: Union[str, None] = 'add_waiver_claims'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pokemon_filters JSONB column to store filter settings
    op.add_column(
        'pool_presets',
        sa.Column('pokemon_filters', postgresql.JSONB, nullable=True)
    )


def downgrade() -> None:
    op.drop_column('pool_presets', 'pokemon_filters')
