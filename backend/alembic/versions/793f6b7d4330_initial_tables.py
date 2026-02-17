"""initial tables

Revision ID: 793f6b7d4330
Revises:
Create Date: 2026-02-16 18:44:48.508503

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "793f6b7d4330"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("riot_puuid", sa.String(78), nullable=False),
        sa.Column("riot_game_name", sa.String(16), nullable=False),
        sa.Column("riot_tag_line", sa.String(5), nullable=False),
        sa.Column("region", sa.String(10), server_default="EUW1"),
        sa.Column("slug", sa.String(25), nullable=False),
        sa.Column("rank_solo_tier", sa.String(15)),
        sa.Column("rank_solo_division", sa.String(5)),
        sa.Column("rank_solo_lp", sa.Integer()),
        sa.Column("rank_solo_wins", sa.Integer()),
        sa.Column("rank_solo_losses", sa.Integer()),
        sa.Column("rank_flex_tier", sa.String(15)),
        sa.Column("rank_flex_division", sa.String(5)),
        sa.Column("primary_role", sa.String(10)),
        sa.Column("secondary_role", sa.String(10)),
        sa.Column("summoner_level", sa.Integer()),
        sa.Column("profile_icon_id", sa.Integer()),
        sa.Column("discord_username", sa.String(50)),
        sa.Column("description", sa.Text()),
        sa.Column("looking_for", sa.String(20)),
        sa.Column("ambition", sa.String(20)),
        sa.Column("languages", postgresql.ARRAY(sa.String())),
        sa.Column("availability", postgresql.JSONB()),
        sa.Column("is_lft", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_riot_sync", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("riot_puuid"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("idx_players_lft", "players", ["is_lft"], postgresql_where=sa.text("is_lft = true"))
    op.create_index("idx_players_role", "players", ["primary_role"])
    op.create_index("idx_players_rank", "players", ["rank_solo_tier"])
    op.create_index(op.f("ix_players_slug"), "players", ["slug"])

    op.create_table(
        "player_champions",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("champion_id", sa.Integer(), nullable=False),
        sa.Column("champion_name", sa.String(30), nullable=False),
        sa.Column("mastery_level", sa.Integer()),
        sa.Column("mastery_points", sa.Integer()),
        sa.Column("games_played", sa.Integer(), server_default="0"),
        sa.Column("wins", sa.Integer(), server_default="0"),
        sa.Column("losses", sa.Integer(), server_default="0"),
        sa.Column("avg_kills", sa.Numeric(4, 1)),
        sa.Column("avg_deaths", sa.Numeric(4, 1)),
        sa.Column("avg_assists", sa.Numeric(4, 1)),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("player_id", "champion_id", name="uq_player_champion"),
    )
    op.create_index("idx_champions_player", "player_champions", ["player_id"])


def downgrade() -> None:
    op.drop_table("player_champions")
    op.drop_table("players")
