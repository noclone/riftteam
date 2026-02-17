import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from shared.constants import ROLE_EMOJIS, ROLE_NAMES

APP_URL = os.getenv("APP_URL", "http://localhost:5173")

log = logging.getLogger("riftteam.lft")

ROLE_CHOICES = [
    app_commands.Choice(name="Top", value="TOP"),
    app_commands.Choice(name="Jungle", value="JUNGLE"),
    app_commands.Choice(name="Mid", value="MIDDLE"),
    app_commands.Choice(name="ADC", value="BOTTOM"),
    app_commands.Choice(name="Support", value="UTILITY"),
]


def _rank_short(tier: str | None, division: str | None) -> str:
    if not tier:
        return "Unranked"
    t = tier.capitalize()
    if division and tier not in ("MASTER", "GRANDMASTER", "CHALLENGER"):
        return f"{t} {division}"
    return t


class LftCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="lft", description="Joueurs qui cherchent une équipe")
    @app_commands.describe(role="Filtrer par rôle")
    @app_commands.choices(role=ROLE_CHOICES)
    async def lft(self, interaction: discord.Interaction, role: app_commands.Choice[str] | None = None) -> None:
        await interaction.response.defer()

        params: dict[str, str] = {"is_lft": "true", "limit": "5"}
        if role:
            params["role"] = role.value

        session = self.bot.http_session  # type: ignore[attr-defined]
        try:
            async with session.get("/api/players", params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception:
            log.exception("Failed to fetch LFT players")
            await interaction.followup.send(
                "Erreur lors de la récupération des joueurs. Réessaie plus tard.",
                ephemeral=True,
            )
            return

        players = data.get("players", [])
        if not players:
            msg = "Aucun joueur LFT trouvé"
            if role:
                msg += f" pour le rôle **{role.name}**"
            msg += "."
            await interaction.followup.send(msg)
            return

        title = "Joueurs LFT"
        if role:
            emoji = ROLE_EMOJIS.get(role.value, "")
            title += f" — {emoji} {role.name}"

        embed = discord.Embed(title=title, color=0x5865F2)

        for p in players:
            riot_id = f"{p['riot_game_name']}#{p['riot_tag_line']}"
            rank = _rank_short(p.get("rank_solo_tier"), p.get("rank_solo_division"))
            primary = p.get("primary_role")
            role_emoji = ROLE_EMOJIS.get(primary, "") if primary else ""
            role_name = ROLE_NAMES.get(primary, "") if primary else ""
            link = f"{APP_URL}/p/{p['slug']}"

            embed.add_field(
                name=riot_id,
                value=f"{rank} · {role_emoji} {role_name}\n[Voir le profil]({link})",
                inline=False,
            )

        embed.set_footer(text=f"RiftTeam · {data.get('total', len(players))} joueurs LFT au total")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LftCog(bot))
