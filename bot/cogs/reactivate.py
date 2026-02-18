import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils import format_api_error, get_api_secret, get_session

log = logging.getLogger("riftteam.reactivate")


class ReactivateCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-reactivate", description="Réactive ton profil et/ou ton équipe désactivés pour inactivité")
    async def rt_reactivate(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        player_msg = await self._reactivate_player(user_id)
        team_msg = await self._reactivate_team(user_id)
        await interaction.followup.send(f"{player_msg}\n{team_msg}")

    async def _reactivate_player(self, user_id: str) -> str:
        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)
        try:
            async with session.get(f"/api/players/by-discord/{user_id}") as resp:
                if resp.status != 200:
                    return "Profil introuvable."
                player = await resp.json()
                if player.get("is_lft"):
                    return "Ton profil est déjà actif."
                async with session.post(
                    f"/api/players/{player['slug']}/reactivate",
                    params={"discord_user_id": user_id},
                    headers={"X-Bot-Secret": api_secret},
                ) as r:
                    if r.status == 200:
                        return "Ton profil LFT a été réactivé !"
                    return "Impossible de réactiver ton profil."
        except Exception as exc:
            log.exception("Failed to reactivate player")
            return format_api_error(exc)

    async def _reactivate_team(self, user_id: str) -> str:
        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)
        try:
            async with session.get(f"/api/teams/by-captain/{user_id}") as resp:
                if resp.status != 200:
                    return "Équipe introuvable."
                team = await resp.json()
                if team.get("is_lfp"):
                    return f"Ton équipe **{team['name']}** est déjà active."
                async with session.post(
                    f"/api/teams/{team['slug']}/reactivate",
                    params={"discord_user_id": user_id},
                    headers={"X-Bot-Secret": api_secret},
                ) as r:
                    if r.status == 200:
                        return f"Ton équipe **{team['name']}** a été réactivée !"
                    return "Impossible de réactiver ton équipe."
        except Exception as exc:
            log.exception("Failed to reactivate team")
            return format_api_error(exc)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")  # type: ignore[union-attr]

        if custom_id.startswith("rt_reactivate_player:"):
            target_id = custom_id[len("rt_reactivate_player:"):]
            if str(interaction.user.id) != target_id:
                await interaction.response.send_message("Ce bouton ne t'est pas destiné.", ephemeral=True)
                return
            await interaction.response.defer()
            msg = await self._reactivate_player(target_id)
            await interaction.edit_original_response(content=msg, view=None)

        elif custom_id.startswith("rt_reactivate_team:"):
            target_id = custom_id[len("rt_reactivate_team:"):]
            if str(interaction.user.id) != target_id:
                await interaction.response.send_message("Ce bouton ne t'est pas destiné.", ephemeral=True)
                return
            await interaction.response.defer()
            msg = await self._reactivate_team(target_id)
            await interaction.edit_original_response(content=msg, view=None)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactivateCog(bot))
