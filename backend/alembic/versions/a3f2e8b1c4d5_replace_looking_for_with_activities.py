"""replace looking_for/ambition/languages/availability with activities/ambiance/frequency

Revision ID: a3f2e8b1c4d5
Revises: 1a1267c7cf3d
Create Date: 2026-02-17 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a3f2e8b1c4d5'
down_revision: str = '1a1267c7cf3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('players', 'looking_for')
    op.drop_column('players', 'ambition')
    op.drop_column('players', 'languages')
    op.drop_column('players', 'availability')

    op.add_column('players', sa.Column('activities', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('players', sa.Column('ambiance', sa.String(10), nullable=True))
    op.add_column('players', sa.Column('frequency_min', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('frequency_max', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('players', 'frequency_max')
    op.drop_column('players', 'frequency_min')
    op.drop_column('players', 'ambiance')
    op.drop_column('players', 'activities')

    op.add_column('players', sa.Column('looking_for', sa.String(20), nullable=True))
    op.add_column('players', sa.Column('ambition', sa.String(20), nullable=True))
    op.add_column('players', sa.Column('languages', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('players', sa.Column('availability', postgresql.JSONB(), nullable=True))
