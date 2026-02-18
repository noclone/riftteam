from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.player import Base


class GuildSettings(Base):
    __tablename__ = "guild_settings"

    guild_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    announcement_channel_id: Mapped[str | None] = mapped_column(String(20))
