import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.player import Base


class RankSnapshot(Base):
    __tablename__ = "rank_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    queue_type: Mapped[str] = mapped_column(String(20), nullable=False)
    tier: Mapped[str | None] = mapped_column(String(15))
    division: Mapped[str | None] = mapped_column(String(5))
    lp: Mapped[int | None] = mapped_column(Integer)
    wins: Mapped[int | None] = mapped_column(Integer)
    losses: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_rank_snapshots_player_time", "player_id", "recorded_at"),
    )


class ChampionSnapshot(Base):
    __tablename__ = "champion_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    champions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    primary_role: Mapped[str | None] = mapped_column(String(10))
    secondary_role: Mapped[str | None] = mapped_column(String(10))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_champion_snapshots_player_time", "player_id", "recorded_at"),
    )
