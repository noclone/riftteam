import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from shared.constants import RANK_ORDER, ROLE_EMOJIS, ROLE_NAMES

ACTIVITY_LABELS: dict[str, str] = {
    "SCRIMS": "Scrims",
    "TOURNOIS": "Tournois",
    "LAN": "LAN",
    "FLEX": "Flex",
    "CLASH": "Clash",
}

AMBIANCE_LABELS: dict[str, str] = {
    "FUN": "For fun",
    "TRYHARD": "Tryhard",
}

APP_URL = os.getenv("APP_URL", "http://localhost:5173")

log = logging.getLogger("riftteam.lfp")

ROLE_CHOICES = [
    app_commands.Choice(name="Top", value="TOP"),
    app_commands.Choice(name="Jungle", value="JUNGLE"),
    app_commands.Choice(name="Mid", value="MIDDLE"),
    app_commands.Choice(name="ADC", value="BOTTOM"),
    app_commands.Choice(name="Support", value="UTILITY"),
]

RANK_CHOICES = [
    app_commands.Choice(name=k.capitalize(), value=k)
    for k in RANK_ORDER
]


def _rank_short(tier: str | None, division: str | None, lp: int | None = None) -> str:
    if not tier:
        return "Unranked"
    t = tier.capitalize()
    if division and tier not in ("MASTER", "GRANDMASTER", "CHALLENGER"):
        base = f"{t} {division}"
    else:
        base = t
    if lp is not None:
        return f"{base} ({lp} LP)"
    return base


class LfpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-lfp", description="Joueurs qui cherchent une équipe")
    @app_commands.describe(
        role="Filtrer par rôle",
        min_rank="Rang minimum",
        max_rank="Rang maximum",
    )
    @app_commands.choices(role=ROLE_CHOICES, min_rank=RANK_CHOICES, max_rank=RANK_CHOICES)
    async def rt_lfp(
        self,
        interaction: discord.Interaction,
        role: app_commands.Choice[str] | None = None,
        min_rank: app_commands.Choice[str] | None = None,
        max_rank: app_commands.Choice[str] | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        params: dict[str, str] = {"is_lft": "true", "limit": "5"}
        if role:
            params["role"] = role.value
        if min_rank:
            params["min_rank"] = min_rank.value
        if max_rank:
            params["max_rank"] = max_rank.value

        session = self.bot.http_session  # type: ignore[attr-defined]
        try:
            async with session.get("/api/players", params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception:
            log.exception("Failed to fetch LFP players")
            await interaction.followup.send(
                "Erreur lors de la récupération des joueurs. Réessaie plus tard.",
                ephemeral=True,
            )
            return

        players = data.get("players", [])
        if not players:
            msg = "Aucun joueur LFT trouvé"
            filters = []
            if role:
                filters.append(f"rôle **{role.name}**")
            if min_rank:
                filters.append(f"rang min **{min_rank.name}**")
            if max_rank:
                filters.append(f"rang max **{max_rank.name}**")
            if filters:
                msg += " pour " + ", ".join(filters)
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
            rank = _rank_short(p.get("rank_solo_tier"), p.get("rank_solo_division"), p.get("rank_solo_lp"))
            primary = p.get("primary_role")
            role_emoji = ROLE_EMOJIS.get(primary, "") if primary else ""
            role_name = ROLE_NAMES.get(primary, "") if primary else ""
            link = f"{APP_URL}/p/{p['slug']}"

            lines = [f"{rank} · {role_emoji} {role_name}"]

            info_parts: list[str] = []
            activities = p.get("activities") or []
            if activities:
                info_parts.append(", ".join(ACTIVITY_LABELS.get(a, a) for a in activities))
            ambiance_val = p.get("ambiance")
            if ambiance_val:
                info_parts.append(AMBIANCE_LABELS.get(ambiance_val, ambiance_val))
            freq_min = p.get("frequency_min")
            freq_max = p.get("frequency_max")
            if freq_min is not None and freq_max is not None:
                info_parts.append(f"{freq_min}-{freq_max}x / semaine")
            if info_parts:
                lines.append(" · ".join(info_parts))

            lines.append(f"[Voir le profil]({link})")

            embed.add_field(
                name=riot_id,
                value="\n".join(lines),
                inline=False,
            )

        embed.set_footer(text=f"RiftTeam · {data.get('total', len(players))} joueurs LFT au total")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LfpCog(bot))
