import aiohttp
import discord
from discord.ext import commands

from shared.constants import ACTIVITY_LABELS, AMBIANCE_LABELS, ROLE_NAMES


def format_api_error(exc: Exception) -> str:
    if isinstance(exc, aiohttp.ClientResponseError):
        if exc.status == 429:
            return "Trop de requêtes. Réessaie dans quelques minutes."
        if exc.status in (502, 503):
            return "Service temporairement indisponible. Réessaie plus tard."
        if exc.status == 500:
            return "Erreur interne du serveur. Réessaie plus tard."
        if exc.status == 403:
            return "Action non autorisée."
    if isinstance(exc, aiohttp.ClientError):
        return "Impossible de contacter le serveur. Réessaie plus tard."
    return "Erreur inattendue. Réessaie plus tard."


def parse_riot_id(riot_id: str) -> tuple[str, str] | None:
    parts = riot_id.split("#", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


def encode_list_filters(role: str | None, min_rank: str | None, max_rank: str | None) -> str:
    return f"{role or ''}:{min_rank or ''}:{max_rank or ''}"


def decode_list_filters(encoded: str) -> tuple[str | None, str | None, str | None]:
    parts = encoded.split(":")
    role = parts[0] or None if len(parts) > 0 else None
    min_rank = parts[1] or None if len(parts) > 1 else None
    max_rank = parts[2] or None if len(parts) > 2 else None
    return role, min_rank, max_rank


def get_session(bot: commands.Bot) -> aiohttp.ClientSession:
    return bot.http_session  # type: ignore[attr-defined]


def get_api_secret(bot: commands.Bot) -> str:
    return bot.api_secret  # type: ignore[attr-defined]


def build_info_parts(entity: dict) -> list[str]:
    parts: list[str] = []
    activities = entity.get("activities") or []
    if activities:
        labels = [ACTIVITY_LABELS.get(a, a) for a in activities]
        parts.append(", ".join(labels))
    ambiance_val = entity.get("ambiance")
    if ambiance_val:
        parts.append(AMBIANCE_LABELS.get(ambiance_val, ambiance_val))
    freq_min = entity.get("frequency_min")
    freq_max = entity.get("frequency_max")
    if freq_min is not None and freq_max is not None:
        parts.append(f"{freq_min}-{freq_max}x / semaine")
    return parts


def create_link_view(label: str, url: str) -> discord.ui.View:
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label=label,
        style=discord.ButtonStyle.link,
        url=url,
    ))
    return view


def build_nav_view(
    prefix: str, page: int, total: int, page_size: int, filters_encoded: str,
) -> discord.ui.View:
    total_pages = max(1, (total + page_size - 1) // page_size)
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(
        label="\u25c0 Pr\u00e9c\u00e9dent",
        style=discord.ButtonStyle.secondary,
        custom_id=f"{prefix}:{page - 1}:{filters_encoded}",
        disabled=page <= 0,
    ))
    view.add_item(discord.ui.Button(
        label="Suivant \u25b6",
        style=discord.ButtonStyle.secondary,
        custom_id=f"{prefix}:{page + 1}:{filters_encoded}",
        disabled=page >= total_pages - 1,
    ))
    return view


def build_no_results_msg(
    entity_name: str,
    role: str | None,
    min_rank: str | None,
    max_rank: str | None,
) -> str:
    msg = f"Aucun {entity_name} trouv\u00e9"
    filters = []
    if role:
        filters.append(f"r\u00f4le **{ROLE_NAMES.get(role, role)}**")
    if min_rank:
        filters.append(f"rang min **{min_rank.capitalize()}**")
    if max_rank:
        filters.append(f"rang max **{max_rank.capitalize()}**")
    if filters:
        msg += " pour " + ", ".join(filters)
    msg += "."
    return msg
