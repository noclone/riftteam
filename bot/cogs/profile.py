import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import APP_URL, RANK_ICON_BASE
from shared.constants import RANK_COLORS, ROLE_EMOJIS, ROLE_NAMES
from shared.format import format_rank, format_win_rate
from utils import build_info_parts, format_api_error, get_session, parse_riot_id

log = logging.getLogger("riftteam.profile")


def _role_display(primary: str | None, secondary: str | None) -> str:
    """Format primary/secondary roles with Discord custom emojis."""
    if not primary:
        return "N/A"
    emoji = ROLE_EMOJIS.get(primary, "")
    name = ROLE_NAMES.get(primary, primary)
    result = f"{emoji} {name}"
    if secondary:
        sec_emoji = ROLE_EMOJIS.get(secondary, "")
        sec_name = ROLE_NAMES.get(secondary, secondary)
        result += f" / {sec_emoji} {sec_name}"
    return result


def _rank_thumbnail(tier: str | None) -> str | None:
    """Return the CommunityDragon rank icon URL, or None if unranked."""
    if not tier:
        return None
    return f"{RANK_ICON_BASE}/{tier.lower()}.png"


def _champion_line(champ: dict) -> str:
    """Format a single champion as a bold name with win rate and games played."""
    name = champ["champion_name"]
    gp = champ.get("games_played", 0)
    wins = champ.get("wins", 0)
    if gp > 0:
        wr = wins / gp * 100
        return f"**{name}** — {wr:.0f}% WR ({gp}G)"
    return f"**{name}**"


def build_profile_embed(player: dict) -> discord.Embed:
    """Build a rich Discord embed for a player profile."""
    tier = player.get("rank_solo_tier")
    color = RANK_COLORS.get(tier, 0x2B2D31) if tier else 0x2B2D31

    title = f"{player['riot_game_name']}#{player['riot_tag_line']}"
    url = f"{APP_URL}/p/{player['slug']}"
    embed = discord.Embed(title=title, url=url, color=color)

    rank_solo = format_rank(tier, player.get("rank_solo_division"), player.get("rank_solo_lp"))
    wr = format_win_rate(player.get("rank_solo_wins"), player.get("rank_solo_losses"), include_games=True)
    rank_display = rank_solo
    if wr:
        rank_display += f" · {wr}"
    embed.add_field(name="Rang Solo/Duo", value=rank_display, inline=True)

    flex_tier = player.get("rank_flex_tier")
    if flex_tier:
        flex_str = format_rank(flex_tier, player.get("rank_flex_division"), player.get("rank_flex_lp"))
        flex_wr = format_win_rate(player.get("rank_flex_wins"), player.get("rank_flex_losses"), include_games=True)
        flex_display = flex_str
        if flex_wr:
            flex_display += f" · {flex_wr}"
        embed.add_field(name="Rang Flex", value=flex_display, inline=True)

    role = _role_display(player.get("primary_role"), player.get("secondary_role"))
    embed.add_field(name="Rôle", value=role, inline=True)

    slug = player["slug"]
    links = (
        f"[OP.GG](https://op.gg/lol/summoners/euw/{slug})"
        f" · [DeepLoL](https://www.deeplol.gg/summoner/EUW/{slug})"
        f" · [DPM](https://dpm.lol/{slug})"
        f" · [LoG](https://www.leagueofgraphs.com/summoner/euw/{slug}#championsData-all-queues)"
    )
    embed.add_field(name="Stats externes", value=links, inline=False)

    info_parts = build_info_parts(player)
    if info_parts:
        embed.add_field(name="Recherche", value=" · ".join(info_parts), inline=False)

    description = player.get("description")
    if description:
        truncated = description[:150] + "…" if len(description) > 150 else description
        embed.add_field(name="Description", value=truncated, inline=False)

    champions = player.get("champions", [])
    if champions:
        sorted_champs = sorted(champions, key=lambda c: c.get("games_played", 0), reverse=True)[:3]
        champ_text = "\n".join(_champion_line(c) for c in sorted_champs)
        embed.add_field(name="Champions", value=champ_text, inline=False)

    thumb = _rank_thumbnail(tier)
    if thumb:
        embed.set_thumbnail(url=thumb)

    sync_dt = player.get("last_riot_sync")
    footer_text = "RiftTeam"
    if sync_dt:
        try:
            dt = datetime.fromisoformat(sync_dt)
            footer_text += f" · Sync {dt.strftime('%d/%m %H:%M')}"
        except (ValueError, TypeError):
            pass
    embed.set_footer(text=footer_text)

    return embed


class ProfileCog(commands.Cog):
    """Slash command to display a player profile embed."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-profil-show", description="Affiche le profil RiftTeam d'un joueur")
    @app_commands.describe(riot_id="Riot ID du joueur (ex: Pseudo#TAG)")
    async def rt_profil(self, interaction: discord.Interaction, riot_id: str) -> None:
        parsed = parse_riot_id(riot_id)
        if not parsed:
            await interaction.response.send_message(
                "Format invalide. Utilise `Pseudo#TAG` (ex: `noclone67#EUW`).",
                ephemeral=True,
            )
            return

        name, tag = parsed
        slug = f"{name}-{tag}"

        await interaction.response.defer(ephemeral=True)

        session = get_session(self.bot)
        try:
            async with session.get(f"/api/players/{slug}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        f"Profil **{riot_id}** introuvable. "
                        f"Utilise `/rt-profil-create {riot_id}` pour le créer !",
                    )
                    return
                resp.raise_for_status()
                player = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch player %s", slug)
            await interaction.followup.send(format_api_error(exc), ephemeral=True)
            return

        embed = build_profile_embed(player)
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProfileCog(bot))
