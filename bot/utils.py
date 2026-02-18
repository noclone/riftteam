import aiohttp
from discord.ext import commands


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
