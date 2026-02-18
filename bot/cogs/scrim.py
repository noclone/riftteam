import logging
import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from zoneinfo import ZoneInfo

from config import APP_URL
from constants import RANK_CHOICES
from shared.constants import RANK_COLORS, ROLE_EMOJIS, ROLE_NAMES
from shared.format import format_rank, format_rank_range
from utils import format_api_error, get_api_secret, get_session

log = logging.getLogger("riftteam.scrim")

PAGE_SIZE = 4
PARIS_TZ = ZoneInfo("Europe/Paris")

FORMAT_CHOICES = [
    app_commands.Choice(name="BO1", value="BO1"),
    app_commands.Choice(name="BO3", value="BO3"),
    app_commands.Choice(name="BO5", value="BO5"),
    app_commands.Choice(name="1 game", value="G1"),
    app_commands.Choice(name="2 games", value="G2"),
    app_commands.Choice(name="3 games", value="G3"),
    app_commands.Choice(name="4 games", value="G4"),
    app_commands.Choice(name="5 games", value="G5"),
]


def _parse_date_parts(date_str: str) -> tuple[int, int, int]:
    date_parts = re.split(r"[/\-.]", date_str)
    if len(date_parts) == 2:
        day, month = int(date_parts[0]), int(date_parts[1])
        year = datetime.now(PARIS_TZ).year
    elif len(date_parts) == 3:
        day, month = int(date_parts[0]), int(date_parts[1])
        year = int(date_parts[2])
        if year < 100:
            year += 2000
    else:
        raise ValueError(f"Format de date invalide : `{date_str}`. Utilise `JJ/MM` ou `JJ/MM/AAAA`.")
    return day, month, year


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    date_str = date_str.strip()
    time_str = time_str.strip()

    m = re.match(r"^(\d{1,2})[hH:]?(\d{0,2})$", time_str)
    if not m:
        raise ValueError(f"Format d'heure invalide : `{time_str}`. Utilise `HH:MM`, `HHhMM` ou `HHh`.")
    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Heure invalide : `{time_str}`.")

    day, month, year = _parse_date_parts(date_str)
    has_year = len(re.split(r"[/\-.]", date_str)) == 3

    try:
        dt = datetime(year, month, day, hour, minute, tzinfo=PARIS_TZ)
    except ValueError:
        raise ValueError(f"Date invalide : `{date_str}` `{time_str}`.")

    now = datetime.now(PARIS_TZ)
    if dt < now and not has_year:
        dt = dt.replace(year=year + 1)

    return dt


def _format_scrim_format(fmt: str | None, game_count: int | None, fearless: bool) -> str:
    if fmt:
        label = fmt
    elif game_count:
        label = f"{game_count} games"
    else:
        label = "BO1"
    if fearless:
        label += " · Fearless"
    return label


def _scrim_info_lines(scrim: dict) -> list[str]:
    scheduled_at = scrim["scheduled_at"]
    if isinstance(scheduled_at, str):
        dt = datetime.fromisoformat(scheduled_at)
    else:
        dt = scheduled_at
    dt_paris = dt.astimezone(PARIS_TZ)
    date_str = dt_paris.strftime("%d/%m")
    hour_str = f"{dt_paris.hour}h{dt_paris.minute:02d}" if dt_paris.minute else f"{dt_paris.hour}h"
    fmt_str = _format_scrim_format(scrim.get("format"), scrim.get("game_count"), scrim.get("fearless", False))
    elo_str = format_rank_range(scrim.get("min_rank"), scrim.get("max_rank"), abbreviated=True)
    return [
        f"\U0001f5d3\ufe0f {date_str}",
        f"\u23f0 {hour_str}",
        f"\u2694\ufe0f {fmt_str}",
        f"\u2705 {elo_str}",
    ]


def _build_scrim_embed(scrim: dict) -> discord.Embed:
    team = scrim["team"]
    min_rank = scrim.get("min_rank")
    max_rank = scrim.get("max_rank")
    tier = min_rank or max_rank
    color = RANK_COLORS.get(tier.upper(), 0xE67E22) if tier else 0xE67E22

    embed = discord.Embed(
        title=f"Scrim — {team['name']}",
        color=color,
    )

    embed.description = "\n".join(_scrim_info_lines(scrim))

    members = team.get("members", [])
    if members:
        roster_lines = []
        for m in members:
            p = m["player"]
            role_emoji = ROLE_EMOJIS.get(m["role"], "")
            rank = format_rank(p.get("rank_solo_tier"), p.get("rank_solo_division"))
            roster_lines.append(f"{role_emoji} **{p['riot_game_name']}**#{p['riot_tag_line']} — {rank}")
        embed.add_field(name=f"Roster ({len(members)}/5)", value="\n".join(roster_lines), inline=False)

    embed.set_footer(text="RiftTeam")
    return embed


def _parse_date(date_str: str) -> str:
    date_str = date_str.strip()
    day, month, year = _parse_date_parts(date_str)
    from datetime import date as date_type
    try:
        d = date_type(year, month, day)
    except ValueError:
        raise ValueError(f"Date invalide : `{date_str}`.")
    return d.isoformat()


def _parse_hour(s: str) -> int:
    s = s.strip().lower().rstrip("h")
    m = re.match(r"^(\d{1,2})(?:[h:](\d{0,2}))?$", s)
    if not m:
        raise ValueError(f"Format d'heure invalide : `{s}`. Utilise `20`, `20h` ou `20:00`.")
    hour = int(m.group(1))
    if not 0 <= hour <= 23:
        raise ValueError(f"Heure invalide : `{s}`.")
    return hour


def _encode_filters(
    min_rank: str | None, max_rank: str | None,
    scheduled_date: str | None, fmt: str | None,
    hour_min: int | None, hour_max: int | None,
) -> str:
    return f"{min_rank or ''}:{max_rank or ''}:{scheduled_date or ''}:{fmt or ''}:{hour_min if hour_min is not None else ''}:{hour_max if hour_max is not None else ''}"


def _decode_filters(encoded: str) -> tuple[str | None, str | None, str | None, str | None, int | None, int | None]:
    parts = encoded.split(":")
    min_rank = parts[0] or None if len(parts) > 0 else None
    max_rank = parts[1] or None if len(parts) > 1 else None
    scheduled_date = parts[2] or None if len(parts) > 2 else None
    fmt = parts[3] or None if len(parts) > 3 else None
    hour_min = int(parts[4]) if len(parts) > 4 and parts[4] else None
    hour_max = int(parts[5]) if len(parts) > 5 and parts[5] else None
    return min_rank, max_rank, scheduled_date, fmt, hour_min, hour_max


class ScrimCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-scrim-post", description="Poste une offre de scrim pour ton équipe")
    @app_commands.describe(
        date="Date du scrim (JJ/MM ou JJ/MM/AAAA)",
        heure="Heure du scrim (HH:MM, HHhMM ou HHh)",
        format="Format du match",
        fearless="Mode Fearless Draft",
        min_rank="Rang minimum accepté",
        max_rank="Rang maximum accepté",
    )
    @app_commands.choices(format=FORMAT_CHOICES, min_rank=RANK_CHOICES, max_rank=RANK_CHOICES)
    async def rt_scrim_post(
        self,
        interaction: discord.Interaction,
        date: str,
        heure: str,
        format: app_commands.Choice[str],
        fearless: bool = False,
        min_rank: app_commands.Choice[str] | None = None,
        max_rank: app_commands.Choice[str] | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)

        try:
            async with session.get(f"/api/teams/by-captain/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        "Tu n'as pas d'équipe. Utilise `/rt-team-create NomEquipe` pour en créer une !",
                        ephemeral=True,
                    )
                    return
                resp.raise_for_status()
                team = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch team")
            await interaction.followup.send(format_api_error(exc), ephemeral=True)
            return

        try:
            dt = _parse_datetime(date, heure)
        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
            return

        now = datetime.now(PARIS_TZ)
        if dt <= now:
            await interaction.followup.send("La date du scrim doit être dans le futur.", ephemeral=True)
            return

        if format.value.startswith("G"):
            fmt_value = None
            game_count = int(format.value[1:])
        else:
            fmt_value = format.value
            game_count = None

        payload = {
            "team_slug": team["slug"],
            "captain_discord_id": str(interaction.user.id),
            "scheduled_at": dt.isoformat(),
            "format": fmt_value,
            "game_count": game_count,
            "fearless": fearless,
            "min_rank": min_rank.value if min_rank else None,
            "max_rank": max_rank.value if max_rank else None,
        }

        try:
            async with session.post(
                "/api/scrims",
                json=payload,
                headers={"X-Bot-Secret": api_secret},
            ) as resp:
                if resp.status == 404:
                    await interaction.followup.send("Équipe introuvable.", ephemeral=True)
                    return
                if resp.status == 403:
                    await interaction.followup.send("Seul le capitaine peut poster un scrim.", ephemeral=True)
                    return
                resp.raise_for_status()
                scrim = await resp.json()
        except discord.NotFound:
            raise
        except Exception as exc:
            log.exception("Failed to create scrim")
            await interaction.followup.send(format_api_error(exc), ephemeral=True)
            return

        embed = _build_scrim_embed(scrim)
        captain_id = team.get("captain_discord_id", str(interaction.user.id))
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Contacter",
            style=discord.ButtonStyle.secondary,
            custom_id=f"rt_contact:{captain_id}",
        ))
        view.add_item(discord.ui.Button(
            label="Voir l'équipe",
            style=discord.ButtonStyle.link,
            url=f"{APP_URL}/t/{team['slug']}",
        ))

        await interaction.channel.send(embed=embed, view=view)  # type: ignore[union-attr]
        await interaction.delete_original_response()

    @app_commands.command(name="rt-scrim-cancel", description="Annule le scrim actif de ton équipe")
    async def rt_scrim_cancel(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)

        try:
            async with session.get(f"/api/teams/by-captain/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        "Tu n'as pas d'équipe.", ephemeral=True,
                    )
                    return
                resp.raise_for_status()
                team = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch team")
            await interaction.followup.send(format_api_error(exc), ephemeral=True)
            return

        try:
            async with session.delete(
                f"/api/scrims/by-team/{team['slug']}",
                headers={"X-Bot-Secret": api_secret},
            ) as resp:
                if resp.status == 404:
                    await interaction.followup.send("Équipe introuvable.", ephemeral=True)
                    return
                resp.raise_for_status()
                data = await resp.json()
        except Exception as exc:
            log.exception("Failed to cancel scrims")
            await interaction.followup.send(format_api_error(exc), ephemeral=True)
            return

        cancelled = data.get("cancelled", 0)
        if cancelled == 0:
            await interaction.followup.send("Aucun scrim actif à annuler.", ephemeral=True)
        else:
            await interaction.followup.send(f"Scrim annulé pour **{team['name']}**.", ephemeral=True)

    @app_commands.command(name="rt-scrim-search", description="Cherche des scrims disponibles")
    @app_commands.describe(
        date="Date (JJ/MM ou JJ/MM/AAAA)",
        heure_min="Heure minimum (ex: 20, 20h, 20:00)",
        heure_max="Heure maximum (ex: 22, 22h, 22:00)",
        format="Format du match",
        min_rank="Rang minimum",
        max_rank="Rang maximum",
    )
    @app_commands.choices(format=FORMAT_CHOICES, min_rank=RANK_CHOICES, max_rank=RANK_CHOICES)
    async def rt_scrim_search(
        self,
        interaction: discord.Interaction,
        date: str | None = None,
        heure_min: str | None = None,
        heure_max: str | None = None,
        format: app_commands.Choice[str] | None = None,
        min_rank: app_commands.Choice[str] | None = None,
        max_rank: app_commands.Choice[str] | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        scheduled_date: str | None = None
        if date:
            try:
                scheduled_date = _parse_date(date)
            except ValueError as e:
                await interaction.followup.send(str(e), ephemeral=True)
                return

        hour_min: int | None = None
        hour_max: int | None = None
        try:
            if heure_min:
                hour_min = _parse_hour(heure_min)
            if heure_max:
                hour_max = _parse_hour(heure_max)
        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
            return

        await self._fetch_scrims_and_respond(
            interaction,
            page=0,
            min_rank=min_rank.value if min_rank else None,
            max_rank=max_rank.value if max_rank else None,
            scheduled_date=scheduled_date,
            fmt=format.value if format else None,
            hour_min=hour_min,
            hour_max=hour_max,
        )

    async def _fetch_scrims_and_respond(
        self,
        interaction: discord.Interaction,
        page: int,
        min_rank: str | None,
        max_rank: str | None,
        scheduled_date: str | None = None,
        fmt: str | None = None,
        hour_min: int | None = None,
        hour_max: int | None = None,
        *,
        edit: bool = False,
    ) -> None:
        params: dict[str, str] = {
            "limit": str(PAGE_SIZE),
            "offset": str(page * PAGE_SIZE),
        }
        if min_rank:
            params["min_rank"] = min_rank
        if max_rank:
            params["max_rank"] = max_rank
        if scheduled_date:
            params["scheduled_date"] = scheduled_date
        if fmt:
            params["format"] = fmt
        if hour_min is not None:
            params["hour_min"] = str(hour_min)
        if hour_max is not None:
            params["hour_max"] = str(hour_max)

        session = get_session(self.bot)
        try:
            async with session.get("/api/scrims", params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch scrims")
            msg = format_api_error(exc)
            if edit:
                await interaction.edit_original_response(content=msg, embed=None, view=None)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return

        scrims = data.get("scrims", [])
        total = data.get("total", len(scrims))

        if not scrims:
            msg = "Aucun scrim disponible"
            filters = []
            if min_rank:
                filters.append(f"rang min **{min_rank.capitalize()}**")
            if max_rank:
                filters.append(f"rang max **{max_rank.capitalize()}**")
            if scheduled_date:
                filters.append(f"date **{scheduled_date}**")
            if fmt:
                filters.append(f"format **{fmt}**")
            if hour_min is not None:
                filters.append(f"heure min **{hour_min}h**")
            if hour_max is not None:
                filters.append(f"heure max **{hour_max}h**")
            if filters:
                msg += " pour " + ", ".join(filters)
            msg += "."
            if edit:
                await interaction.edit_original_response(content=msg, embed=None, view=None)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return

        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        embed = discord.Embed(title="Scrims disponibles", color=0xE67E22)

        seen_captains: set[str] = set()
        contact_buttons: list[tuple[str, str]] = []

        for i, s in enumerate(scrims):
            team = s["team"]
            team_name = team["name"]
            captain_id = s.get("captain_discord_id", "")

            embed.add_field(name=team_name, value="\n".join(_scrim_info_lines(s)), inline=True)

            if i % 2 == 1:
                embed.add_field(name="\u200b", value="\u200b", inline=True)

            if captain_id and captain_id not in seen_captains:
                seen_captains.add(captain_id)
                contact_buttons.append((captain_id, team_name))

        if len(scrims) % 2 == 1:
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.set_footer(text=f"Page {page + 1}/{total_pages} · {total} scrims au total")

        filters_encoded = _encode_filters(min_rank, max_rank, scheduled_date, fmt, hour_min, hour_max)
        view = discord.ui.View(timeout=None)

        for captain_id, team_name in contact_buttons:
            label = f"Contacter {team_name}"
            if len(label) > 80:
                label = label[:77] + "..."
            view.add_item(discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"rt_contact:{captain_id}",
            ))

        view.add_item(discord.ui.Button(
            label="◀ Précédent",
            style=discord.ButtonStyle.secondary,
            custom_id=f"rt_scrim_page:{page - 1}:{filters_encoded}",
            disabled=page <= 0,
        ))
        view.add_item(discord.ui.Button(
            label="Suivant ▶",
            style=discord.ButtonStyle.secondary,
            custom_id=f"rt_scrim_page:{page + 1}:{filters_encoded}",
            disabled=page >= total_pages - 1,
        ))

        if edit:
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")  # type: ignore[union-attr]
        if not custom_id.startswith("rt_scrim_page:"):
            return

        parts = custom_id[len("rt_scrim_page:"):].split(":", 1)
        try:
            page = int(parts[0])
        except (ValueError, IndexError):
            return
        min_rank, max_rank, scheduled_date, fmt, hour_min, hour_max = _decode_filters(parts[1]) if len(parts) > 1 else (None, None, None, None, None, None)

        await interaction.response.defer(ephemeral=True)
        await self._fetch_scrims_and_respond(interaction, page, min_rank, max_rank, scheduled_date, fmt, hour_min, hour_max, edit=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ScrimCog(bot))
