import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils import format_api_error, get_api_secret, get_session

log = logging.getLogger("riftteam.reactivate")


class ReactivateCog(commands.Cog):
    """Slash commands and button handlers to reactivate inactive profiles/teams."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-profil-enable-lft", description="Active ton profil en mode LFT (cherche une équipe)")
    async def rt_profil_enable_lft(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        msg = await self._reactivate_player(str(interaction.user.id))
        await interaction.followup.send(msg)

    @app_commands.command(name="rt-team-enable-lfp", description="Active ton équipe en mode LFP (cherche des joueurs)")
    async def rt_team_enable_lfp(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        msg = await self._reactivate_team(str(interaction.user.id))
        await interaction.followup.send(msg)

    async def _reactivate_player(self, user_id: str) -> str:
        """Re-enable LFT status for a player via the backend API."""
        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)
        try:
            async with session.get(f"/api/players/by-discord/{user_id}") as resp:
                if resp.status != 200:
                    return "Profil introuvable."
                player = await resp.json()
                if player.get("is_lft"):
                    return "Ton profil est déjà en mode LFT."
                async with session.post(
                    f"/api/players/{player['slug']}/reactivate",
                    params={"discord_user_id": user_id},
                    headers={"X-Bot-Secret": api_secret},
                ) as r:
                    if r.status == 200:
                        return "Ton profil est maintenant en mode LFT !"
                    return "Impossible d'activer le mode LFT."
        except Exception as exc:
            log.exception("Failed to reactivate player")
            return format_api_error(exc)

    async def _reactivate_team(self, user_id: str) -> str:
        """Re-enable LFP status for a team via the backend API."""
        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)
        try:
            async with session.get(f"/api/teams/by-captain/{user_id}") as resp:
                if resp.status != 200:
                    return "Équipe introuvable."
                team = await resp.json()
                if team.get("is_lfp"):
                    return f"Ton équipe **{team['name']}** est déjà en mode LFP."
                async with session.post(
                    f"/api/teams/{team['slug']}/reactivate",
                    params={"discord_user_id": user_id},
                    headers={"X-Bot-Secret": api_secret},
                ) as r:
                    if r.status == 200:
                        return f"Ton équipe **{team['name']}** est maintenant en mode LFP !"
                    return "Impossible d'activer le mode LFP."
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
