"""add teams

Revision ID: d6e5f1a2b3c4
Revises: c5d4e0f3a7b8
Create Date: 2026-02-17 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd6e5f1a2b3c4'
down_revision: str = 'c5d4e0f3a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'teams',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('slug', sa.String(55), nullable=False),
        sa.Column('captain_discord_id', sa.String(20), nullable=False),
        sa.Column('captain_discord_name', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('activities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('ambiance', sa.String(10), nullable=True),
        sa.Column('frequency_min', sa.Integer(), nullable=True),
        sa.Column('frequency_max', sa.Integer(), nullable=True),
        sa.Column('wanted_roles', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('min_rank', sa.String(15), nullable=True),
        sa.Column('max_rank', sa.String(15), nullable=True),
        sa.Column('is_lfp', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('captain_discord_id'),
    )
    op.create_index('idx_teams_slug', 'teams', ['slug'])
    op.create_index('idx_teams_lfp', 'teams', ['is_lfp'], postgresql_where=sa.text('is_lfp = true'))

    op.create_table(
        'team_members',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.Column('player_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(10), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('player_id', name='uq_team_members_player'),
    )


def downgrade() -> None:
    op.drop_table('team_members')
    op.drop_index('idx_teams_lfp', table_name='teams')
    op.drop_index('idx_teams_slug', table_name='teams')
    op.drop_table('teams')
