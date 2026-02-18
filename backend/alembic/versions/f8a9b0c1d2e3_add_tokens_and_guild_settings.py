"""add action_tokens and guild_settings

Revision ID: f8a9b0c1d2e3
Revises: e7f6a3b4c5d8
Create Date: 2026-02-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f8a9b0c1d2e3'
down_revision: str = 'e7f6a3b4c5d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'action_tokens',
        sa.Column('token', sa.String(32), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('discord_user_id', sa.String(20), nullable=False),
        sa.Column('discord_username', sa.String(100), nullable=False),
        sa.Column('game_name', sa.String(50), nullable=True),
        sa.Column('tag_line', sa.String(10), nullable=True),
        sa.Column('slug', sa.String(100), nullable=True),
        sa.Column('team_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('token'),
    )

    op.create_table(
        'guild_settings',
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('announcement_channel_id', sa.String(20), nullable=True),
        sa.PrimaryKeyConstraint('guild_id'),
    )


def downgrade() -> None:
    op.drop_table('guild_settings')
    op.drop_table('action_tokens')
