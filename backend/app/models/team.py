import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.player import Base


class Team(Base):
    """A team created by a captain, with roster members and LFP settings."""

    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String(55), unique=True, nullable=False, index=True)
    captain_discord_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    captain_discord_name: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    activities: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=[])
    ambiance: Mapped[str | None] = mapped_column(String(10))
    frequency_min: Mapped[int | None] = mapped_column(Integer)
    frequency_max: Mapped[int | None] = mapped_column(Integer)
    wanted_roles: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=[])
    min_rank: Mapped[str | None] = mapped_column(String(15))
    max_rank: Mapped[str | None] = mapped_column(String(15))
    is_lfp: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_teams_lfp", "is_lfp", postgresql_where=is_lfp.is_(True)),
    )

    @staticmethod
    def make_slug(name: str) -> str:
        """Generate a URL-safe slug from the team name."""
        return name.lower().replace(" ", "-")


class TeamMember(Base):
    """Association between a player and their team with an assigned role."""

    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)

    team = relationship("Team", back_populates="members")
    player = relationship("Player")

    __table_args__ = (
        UniqueConstraint("player_id", name="uq_team_members_player"),
    )
