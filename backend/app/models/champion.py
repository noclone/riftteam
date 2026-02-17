import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.player import Base


class PlayerChampion(Base):
    __tablename__ = "player_champions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), index=True)
    champion_id: Mapped[int] = mapped_column(Integer, nullable=False)
    champion_name: Mapped[str] = mapped_column(String(30), nullable=False)

    mastery_level: Mapped[int | None] = mapped_column(Integer)
    mastery_points: Mapped[int | None] = mapped_column(Integer)

    games_played: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    avg_kills: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    avg_deaths: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    avg_assists: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))

    player = relationship("Player", back_populates="champions")

    __table_args__ = (
        UniqueConstraint("player_id", "champion_id", name="uq_player_champion"),
    )
