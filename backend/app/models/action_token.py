from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.player import Base


class ActionToken(Base):
    __tablename__ = "action_tokens"

    token: Mapped[str] = mapped_column(String(32), primary_key=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    discord_user_id: Mapped[str] = mapped_column(String(20), nullable=False)
    discord_username: Mapped[str] = mapped_column(String(100), nullable=False)
    game_name: Mapped[str | None] = mapped_column(String(50))
    tag_line: Mapped[str | None] = mapped_column(String(10))
    slug: Mapped[str | None] = mapped_column(String(100))
    team_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
