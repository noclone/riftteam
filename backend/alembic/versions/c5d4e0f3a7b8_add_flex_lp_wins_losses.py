"""add flex lp wins losses

Revision ID: c5d4e0f3a7b8
Revises: b4c3d9e2f5a6
Create Date: 2026-02-17 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c5d4e0f3a7b8'
down_revision: str = 'b4c3d9e2f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('players', sa.Column('rank_flex_lp', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('rank_flex_wins', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('rank_flex_losses', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('players', 'rank_flex_losses')
    op.drop_column('players', 'rank_flex_wins')
    op.drop_column('players', 'rank_flex_lp')
