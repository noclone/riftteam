import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.player import Base


class Scrim(Base):
    """A scheduled scrim request posted by a team captain."""

    __tablename__ = "scrims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    captain_discord_id: Mapped[str] = mapped_column(String(20), nullable=False)
    min_rank: Mapped[str | None] = mapped_column(String(15))
    max_rank: Mapped[str | None] = mapped_column(String(15))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    format: Mapped[str | None] = mapped_column(String(10))
    game_count: Mapped[int | None] = mapped_column(Integer)
    fearless: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    team = relationship("Team")

    __table_args__ = (
        Index("idx_scrims_active_scheduled", "is_active", "scheduled_at"),
    )
