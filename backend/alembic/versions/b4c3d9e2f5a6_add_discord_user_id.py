"""add discord_user_id to players

Revision ID: b4c3d9e2f5a6
Revises: a3f2e8b1c4d5
Create Date: 2026-02-17 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b4c3d9e2f5a6'
down_revision: str = 'a3f2e8b1c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('players', sa.Column('discord_user_id', sa.String(20), nullable=True))
    op.create_unique_constraint('uq_players_discord_user_id', 'players', ['discord_user_id'])


def downgrade() -> None:
    op.drop_constraint('uq_players_discord_user_id', 'players', type_='unique')
    op.drop_column('players', 'discord_user_id')
