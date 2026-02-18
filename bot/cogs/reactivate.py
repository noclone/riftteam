import logging

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("riftteam.reactivate")


class ReactivateCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-reactivate", description="Réactive ton profil et/ou ton équipe désactivés pour inactivité")
    async def rt_reactivate(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        session = self.bot.http_session  # type: ignore[attr-defined]
        api_secret = self.bot.api_secret  # type: ignore[attr-defined]
        user_id = str(interaction.user.id)
        messages: list[str] = []

        try:
            async with session.get(f"/api/players/by-discord/{user_id}") as resp:
                if resp.status == 200:
                    player = await resp.json()
                    if not player.get("is_lft"):
                        async with session.post(
                            f"/api/players/{player['slug']}/reactivate",
                            params={"discord_user_id": user_id},
                            headers={"X-Bot-Secret": api_secret},
                        ) as reactivate_resp:
                            if reactivate_resp.status == 200:
                                messages.append("Ton profil LFT a été réactivé !")
                            else:
                                messages.append("Impossible de réactiver ton profil.")
                    else:
                        messages.append("Ton profil est déjà actif.")
        except Exception:
            log.exception("Failed to check/reactivate player")
            messages.append("Erreur lors de la vérification de ton profil.")

        try:
            async with session.get(f"/api/teams/by-captain/{user_id}") as resp:
                if resp.status == 200:
                    team = await resp.json()
                    if not team.get("is_lfp"):
                        async with session.post(
                            f"/api/teams/{team['slug']}/reactivate",
                            params={"discord_user_id": user_id},
                            headers={"X-Bot-Secret": api_secret},
                        ) as reactivate_resp:
                            if reactivate_resp.status == 200:
                                messages.append(f"Ton équipe **{team['name']}** a été réactivée !")
                            else:
                                messages.append("Impossible de réactiver ton équipe.")
                    else:
                        messages.append(f"Ton équipe **{team['name']}** est déjà active.")
        except Exception:
            log.exception("Failed to check/reactivate team")
            messages.append("Erreur lors de la vérification de ton équipe.")

        if not messages:
            messages.append("Aucun profil ni équipe à réactiver.")

        await interaction.followup.send("\n".join(messages))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactivateCog(bot))
