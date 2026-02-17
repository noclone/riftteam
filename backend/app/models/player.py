import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    riot_puuid: Mapped[str] = mapped_column(String(78), unique=True, nullable=False)
    riot_game_name: Mapped[str] = mapped_column(String(16), nullable=False)
    riot_tag_line: Mapped[str] = mapped_column(String(5), nullable=False)
    region: Mapped[str] = mapped_column(String(10), default="EUW1")
    slug: Mapped[str] = mapped_column(String(25), unique=True, nullable=False, index=True)

    rank_solo_tier: Mapped[str | None] = mapped_column(String(15))
    rank_solo_division: Mapped[str | None] = mapped_column(String(5))
    rank_solo_lp: Mapped[int | None] = mapped_column(Integer)
    rank_solo_wins: Mapped[int | None] = mapped_column(Integer)
    rank_solo_losses: Mapped[int | None] = mapped_column(Integer)
    rank_flex_tier: Mapped[str | None] = mapped_column(String(15))
    rank_flex_division: Mapped[str | None] = mapped_column(String(5))
    rank_flex_lp: Mapped[int | None] = mapped_column(Integer)
    rank_flex_wins: Mapped[int | None] = mapped_column(Integer)
    rank_flex_losses: Mapped[int | None] = mapped_column(Integer)
    peak_solo_tier: Mapped[str | None] = mapped_column(String(15))
    peak_solo_division: Mapped[str | None] = mapped_column(String(5))
    peak_solo_lp: Mapped[int | None] = mapped_column(Integer)
    primary_role: Mapped[str | None] = mapped_column(String(10))
    secondary_role: Mapped[str | None] = mapped_column(String(10))
    summoner_level: Mapped[int | None] = mapped_column(Integer)
    profile_icon_id: Mapped[int | None] = mapped_column(Integer)

    discord_user_id: Mapped[str | None] = mapped_column(String(20), unique=True)
    discord_username: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    activities: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=[])
    ambiance: Mapped[str | None] = mapped_column(String(10))
    frequency_min: Mapped[int | None] = mapped_column(Integer)
    frequency_max: Mapped[int | None] = mapped_column(Integer)

    is_lft: Mapped[bool] = mapped_column(Boolean, default=True)
    last_riot_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    champions = relationship("PlayerChampion", back_populates="player", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_players_lft", "is_lft", postgresql_where=(is_lft == True)),
        Index("idx_players_role", "primary_role"),
        Index("idx_players_rank", "rank_solo_tier"),
    )

    @staticmethod
    def make_slug(game_name: str, tag_line: str) -> str:
        return f"{game_name}-{tag_line}"
