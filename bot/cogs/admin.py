import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils import format_api_error

log = logging.getLogger("riftteam.admin")


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-setup", description="Configure le channel d'annonces RiftTeam")
    @app_commands.default_permissions(manage_guild=True)
    async def rt_setup(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        session = self.bot.http_session  # type: ignore[attr-defined]
        api_secret = self.bot.api_secret  # type: ignore[attr-defined]

        try:
            async with session.put(
                f"/api/guild-settings/{interaction.guild.id}",
                json={"announcement_channel_id": str(interaction.channel_id)},
                headers={"X-Bot-Secret": api_secret},
            ) as resp:
                resp.raise_for_status()
        except Exception as exc:
            log.exception("Failed to save guild settings")
            await interaction.followup.send(format_api_error(exc), ephemeral=True)
            return

        log.info("Announcement channel set to %d for guild %d", interaction.channel_id, interaction.guild.id)
        await interaction.followup.send(
            f"Les annonces RiftTeam seront envoyées dans <#{interaction.channel_id}>.",
            ephemeral=True,
        )


async def get_announcement_channel(bot: commands.Bot, guild_id: int) -> int | None:
    session = bot.http_session  # type: ignore[attr-defined]
    try:
        async with session.get(f"/api/guild-settings/{guild_id}") as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            data = await resp.json()
            ch = data.get("announcement_channel_id")
            return int(ch) if ch else None
    except Exception:
        return None


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
