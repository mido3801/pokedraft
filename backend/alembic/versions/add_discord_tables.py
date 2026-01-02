"""Add Discord bot tables

Revision ID: add_discord_tables
Revises: add_preset_filters
Create Date: 2026-01-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_discord_tables'
down_revision: Union[str, None] = 'add_preset_filters'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create remindertype enum
    reminder_type = postgresql.ENUM(
        'match_personal', 'match_league', 'draft_starting', 'waiver_deadline',
        name='remindertype',
        create_type=False
    )
    reminder_type.create(op.get_bind(), checkfirst=True)

    # Create discord_guild_configs table
    op.create_table(
        'discord_guild_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('guild_id', sa.String(50), nullable=False, index=True),
        sa.Column('league_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leagues.id'), nullable=False),
        sa.Column('notification_channel_id', sa.String(50), nullable=True),
        sa.Column('match_reminder_channel_id', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Create unique constraint for guild_id + league_id
    op.create_unique_constraint(
        'uq_discord_guild_config_guild_league',
        'discord_guild_configs',
        ['guild_id', 'league_id']
    )

    # Create indexes
    op.create_index('ix_discord_guild_configs_league_id', 'discord_guild_configs', ['league_id'])

    # Create user_notification_settings table
    op.create_table(
        'user_notification_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('dm_match_reminders', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('dm_trade_notifications', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('dm_waiver_notifications', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('dm_draft_notifications', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('match_reminder_hours_before', sa.Integer, nullable=False, server_default='24'),
        sa.Column('require_confirmation_for_trades', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('require_confirmation_for_waivers', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Create index on user_id
    op.create_index('ix_user_notification_settings_user_id', 'user_notification_settings', ['user_id'])

    # Create scheduled_reminders table
    op.create_table(
        'scheduled_reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('reminder_type', postgresql.ENUM(
            'match_personal', 'match_league', 'draft_starting', 'waiver_deadline',
            name='remindertype', create_type=False
        ), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('scheduled_for', sa.DateTime, nullable=False, index=True),
        sa.Column('sent_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for scheduled_reminders
    op.create_index('ix_scheduled_reminders_target_id', 'scheduled_reminders', ['target_id'])
    op.create_index('ix_scheduled_reminders_target_user_id', 'scheduled_reminders', ['target_user_id'])
    op.create_index(
        'ix_scheduled_reminders_pending',
        'scheduled_reminders',
        ['scheduled_for'],
        postgresql_where=sa.text('sent_at IS NULL')
    )


def downgrade() -> None:
    # Drop scheduled_reminders table
    op.drop_index('ix_scheduled_reminders_pending', table_name='scheduled_reminders')
    op.drop_index('ix_scheduled_reminders_target_user_id', table_name='scheduled_reminders')
    op.drop_index('ix_scheduled_reminders_target_id', table_name='scheduled_reminders')
    op.drop_table('scheduled_reminders')

    # Drop user_notification_settings table
    op.drop_index('ix_user_notification_settings_user_id', table_name='user_notification_settings')
    op.drop_table('user_notification_settings')

    # Drop discord_guild_configs table
    op.drop_index('ix_discord_guild_configs_league_id', table_name='discord_guild_configs')
    op.drop_constraint('uq_discord_guild_config_guild_league', 'discord_guild_configs', type_='unique')
    op.drop_table('discord_guild_configs')

    # Drop enum
    op.execute('DROP TYPE IF EXISTS remindertype')
