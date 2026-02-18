from fastapi import Header, HTTPException, Request

from app.config import settings
from shared.riot_client import RiotClient


async def verify_bot_secret(x_bot_secret: str = Header(...)) -> str:
    """Validate the X-Bot-Secret header against the configured secret."""
    if x_bot_secret != settings.bot_api_secret:
        raise HTTPException(403, "Invalid bot secret")
    return x_bot_secret


def get_riot_client(request: Request) -> RiotClient:
    """Return the shared RiotClient from app state, or create a temporary one."""
    client = getattr(request.app.state, "riot_client", None)
    if client:
        return client
    if not settings.riot_api_key:
        raise HTTPException(503, "Riot API key not configured")
    return RiotClient(settings.riot_api_key)
