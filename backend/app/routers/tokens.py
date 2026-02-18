from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import verify_bot_secret
from app.services.token_store import create_token, validate_token

router = APIRouter(tags=["tokens"])


class TokenCreateRequest(BaseModel):
    action: Literal["create", "edit", "team_create", "team_edit"]
    discord_user_id: str
    discord_username: str
    game_name: str | None = None
    tag_line: str | None = None
    slug: str | None = None
    team_name: str | None = None


class TokenCreateResponse(BaseModel):
    token: str
    url: str


class TokenValidateResponse(BaseModel):
    action: str
    discord_username: str
    game_name: str | None = None
    tag_line: str | None = None
    slug: str | None = None
    team_name: str | None = None


@router.post("/tokens", response_model=TokenCreateResponse)
async def create_token_endpoint(
    body: TokenCreateRequest,
    _: str = Depends(verify_bot_secret),
    db: AsyncSession = Depends(get_db),
):

    data = await create_token(
        db,
        action=body.action,
        discord_user_id=body.discord_user_id,
        discord_username=body.discord_username,
        game_name=body.game_name,
        tag_line=body.tag_line,
        slug=body.slug,
        team_name=body.team_name,
    )

    paths = {
        "create": "/create",
        "edit": "/edit",
        "team_create": "/team/create",
        "team_edit": "/team/edit",
    }
    path = paths[body.action]
    url = f"{settings.app_url}{path}?token={data.token}"

    return TokenCreateResponse(token=data.token, url=url)


@router.get("/tokens/{token}/validate", response_model=TokenValidateResponse)
async def validate_token_endpoint(token: str, db: AsyncSession = Depends(get_db)):
    data = await validate_token(db, token)
    if data is None:
        raise HTTPException(404, "Token invalide ou expiré")

    return TokenValidateResponse(
        action=data.action,
        discord_username=data.discord_username,
        game_name=data.game_name,
        tag_line=data.tag_line,
        slug=data.slug,
        team_name=data.team_name,
    )
