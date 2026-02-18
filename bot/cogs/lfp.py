import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import APP_URL
from constants import RANK_CHOICES, ROLE_CHOICES
from shared.constants import ROLE_EMOJIS, ROLE_NAMES
from shared.format import format_rank
from utils import build_info_parts, build_nav_view, build_no_results_msg, decode_list_filters, encode_list_filters, format_api_error, get_session

log = logging.getLogger("riftteam.lfp")

PAGE_SIZE = 5


def _build_embed(players: list[dict], total: int, page: int, role: str | None) -> discord.Embed:
    title = "Joueurs LFT"
    if role:
        emoji = ROLE_EMOJIS.get(role, "")
        name = ROLE_NAMES.get(role, role)
        title += f" — {emoji} {name}"

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    embed = discord.Embed(title=title, color=0x5865F2)

    for p in players:
        riot_id = f"{p['riot_game_name']}#{p['riot_tag_line']}"
        rank = format_rank(p.get("rank_solo_tier"), p.get("rank_solo_division"), p.get("rank_solo_lp"))
        primary = p.get("primary_role")
        secondary = p.get("secondary_role")
        role_str = f"{ROLE_EMOJIS.get(primary, '')} {ROLE_NAMES.get(primary, '')}" if primary else ""
        if secondary:
            role_str += f" / {ROLE_EMOJIS.get(secondary, '')} {ROLE_NAMES.get(secondary, '')}"
        link = f"{APP_URL}/p/{p['slug']}"

        lines = [f"{rank} · {role_str}"]

        info_parts = build_info_parts(p)
        if info_parts:
            lines.append(" · ".join(info_parts))

        lines.append(f"[Voir le profil]({link})")

        embed.add_field(name=riot_id, value="\n".join(lines), inline=False)

    embed.set_footer(text=f"Page {page + 1}/{total_pages} · {total} joueurs LFT au total")
    return embed


class LfpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _fetch_and_respond(
        self,
        interaction: discord.Interaction,
        page: int,
        role: str | None,
        min_rank: str | None,
        max_rank: str | None,
        *,
        edit: bool = False,
    ) -> None:
        params: dict[str, str] = {
            "is_lft": "true",
            "limit": str(PAGE_SIZE),
            "offset": str(page * PAGE_SIZE),
        }
        if role:
            params["role"] = role
        if min_rank:
            params["min_rank"] = min_rank
        if max_rank:
            params["max_rank"] = max_rank

        session = get_session(self.bot)
        try:
            async with session.get("/api/players", params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch LFP players")
            msg = format_api_error(exc)
            if edit:
                await interaction.edit_original_response(content=msg, embed=None, view=None)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return

        players = data.get("players", [])
        total = data.get("total", len(players))

        if not players:
            msg = build_no_results_msg("joueur LFT", role, min_rank, max_rank)
            if edit:
                await interaction.edit_original_response(content=msg, embed=None, view=None)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return

        embed = _build_embed(players, total, page, role)
        filters_encoded = encode_list_filters(role, min_rank, max_rank)
        view = build_nav_view("rt_lfp_page", page, total, PAGE_SIZE, filters_encoded)

        for p in players:
            discord_id = p.get("discord_user_id")
            if discord_id:
                riot_id = f"{p['riot_game_name']}#{p['riot_tag_line']}"
                label = f"Contacter {riot_id}"
                if len(label) > 80:
                    label = label[:77] + "..."
                view.add_item(discord.ui.Button(
                    label=label,
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"rt_contact:{discord_id}",
                ))

        if edit:
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

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
        await self._fetch_and_respond(
            interaction,
            page=0,
            role=role.value if role else None,
            min_rank=min_rank.value if min_rank else None,
            max_rank=max_rank.value if max_rank else None,
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")  # type: ignore[union-attr]
        if not custom_id.startswith("rt_lfp_page:"):
            return

        parts = custom_id[len("rt_lfp_page:"):].split(":", 1)
        try:
            page = int(parts[0])
        except (ValueError, IndexError):
            return
        role, min_rank, max_rank = decode_list_filters(parts[1]) if len(parts) > 1 else (None, None, None)

        await interaction.response.defer(ephemeral=True)
        await self._fetch_and_respond(interaction, page, role, min_rank, max_rank, edit=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LfpCog(bot))
