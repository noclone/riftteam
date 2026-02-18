"""add scrims

Revision ID: e7f6a3b4c5d8
Revises: d6e5f1a2b3c4
Create Date: 2026-02-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e7f6a3b4c5d8'
down_revision: str = 'd6e5f1a2b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scrims',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.Column('captain_discord_id', sa.String(20), nullable=False),
        sa.Column('min_rank', sa.String(15), nullable=True),
        sa.Column('max_rank', sa.String(15), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('format', sa.String(10), nullable=True),
        sa.Column('game_count', sa.Integer(), nullable=True),
        sa.Column('fearless', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_scrims_active_scheduled', 'scrims', ['is_active', 'scheduled_at'])


def downgrade() -> None:
    op.drop_index('idx_scrims_active_scheduled', table_name='scrims')
    op.drop_table('scrims')
