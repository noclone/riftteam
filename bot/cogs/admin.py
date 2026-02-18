import logging

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("riftteam.admin")

announcement_channels: dict[int, int] = {}


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-setup", description="Configure le channel d'annonces RiftTeam")
    @app_commands.default_permissions(manage_guild=True)
    async def rt_setup(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        announcement_channels[interaction.guild.id] = interaction.channel_id
        log.info("Announcement channel set to %d for guild %d", interaction.channel_id, interaction.guild.id)
        await interaction.response.send_message(
            f"Les annonces RiftTeam seront envoyées dans <#{interaction.channel_id}>.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
