from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.token_store import create_token, validate_token

router = APIRouter(tags=["tokens"])


class TokenCreateRequest(BaseModel):
    action: Literal["create", "edit"]
    discord_user_id: str
    discord_username: str
    game_name: str | None = None
    tag_line: str | None = None
    slug: str | None = None


class TokenCreateResponse(BaseModel):
    token: str
    url: str


class TokenValidateResponse(BaseModel):
    action: str
    discord_username: str
    game_name: str | None = None
    tag_line: str | None = None
    slug: str | None = None


@router.post("/tokens", response_model=TokenCreateResponse)
async def create_token_endpoint(
    body: TokenCreateRequest,
    x_bot_secret: str = Header(...),
):
    if x_bot_secret != settings.bot_api_secret:
        raise HTTPException(403, "Invalid bot secret")

    data = create_token(
        action=body.action,
        discord_user_id=body.discord_user_id,
        discord_username=body.discord_username,
        game_name=body.game_name,
        tag_line=body.tag_line,
        slug=body.slug,
    )

    path = "/create" if body.action == "create" else "/edit"
    url = f"{settings.app_url}{path}?token={data.token}"

    return TokenCreateResponse(token=data.token, url=url)


@router.get("/tokens/{token}/validate", response_model=TokenValidateResponse)
async def validate_token_endpoint(token: str):
    data = validate_token(token)
    if data is None:
        raise HTTPException(404, "Token invalide ou expiré")

    return TokenValidateResponse(
        action=data.action,
        discord_username=data.discord_username,
        game_name=data.game_name,
        tag_line=data.tag_line,
        slug=data.slug,
    )
