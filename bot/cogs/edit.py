import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils import create_link_view, format_api_error, get_api_secret, get_session

log = logging.getLogger("riftteam.edit")


class EditCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-profil-edit", description="Modifie ton profil RiftTeam")
    async def rt_edit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)

        try:
            async with session.get(f"/api/players/by-discord/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        "Tu n'as pas encore de profil. Utilise `/rt-profil-create Pseudo#TAG` pour en créer un !",
                    )
                    return
                resp.raise_for_status()
                player = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch player by discord ID")
            await interaction.followup.send(format_api_error(exc))
            return

        try:
            payload = {
                "action": "edit",
                "discord_user_id": str(interaction.user.id),
                "discord_username": interaction.user.name,
                "slug": player["slug"],
            }
            async with session.post(
                "/api/tokens",
                json=payload,
                headers={"X-Bot-Secret": api_secret},
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                url = data["url"]
        except Exception as exc:
            log.exception("Failed to create edit token")
            await interaction.followup.send(format_api_error(exc))
            return

        riot_id = f"{player['riot_game_name']}#{player['riot_tag_line']}"
        view = create_link_view("Modifier mon profil", url)
        await interaction.followup.send(
            f"Clique ci-dessous pour modifier ton profil **{riot_id}** !\n"
            f"Le lien expire dans 30 minutes.",
            view=view,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EditCog(bot))
