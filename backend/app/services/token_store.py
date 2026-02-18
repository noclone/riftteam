import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_token import ActionToken

TOKEN_TTL = timedelta(minutes=30)


async def _cleanup(db: AsyncSession) -> None:
    """Delete action tokens older than TOKEN_TTL."""
    cutoff = datetime.now(UTC) - TOKEN_TTL
    await db.execute(delete(ActionToken).where(ActionToken.created_at < cutoff))


async def create_token(
    db: AsyncSession,
    *,
    action: str,
    discord_user_id: str,
    discord_username: str,
    game_name: str | None = None,
    tag_line: str | None = None,
    slug: str | None = None,
    team_name: str | None = None,
) -> ActionToken:
    """Generate a new action token and persist it after cleaning up expired ones."""
    await _cleanup(db)
    token = uuid.uuid4().hex
    obj = ActionToken(
        token=token,
        action=action,
        discord_user_id=discord_user_id,
        discord_username=discord_username,
        game_name=game_name,
        tag_line=tag_line,
        slug=slug,
        team_name=team_name,
        created_at=datetime.now(UTC),
    )
    db.add(obj)
    await db.commit()
    return obj


async def validate_token(db: AsyncSession, token: str) -> ActionToken | None:
    """Return the token if it exists and hasn't expired, else None."""
    await _cleanup(db)
    result = await db.execute(select(ActionToken).where(ActionToken.token == token))
    return result.scalar_one_or_none()


async def consume_token(db: AsyncSession, token: str, expected_action: str) -> ActionToken | None:
    """Validate and delete a token in one step, returning it if valid."""
    await _cleanup(db)
    result = await db.execute(select(ActionToken).where(ActionToken.token == token))
    obj = result.scalar_one_or_none()
    if obj is None or obj.action != expected_action:
        return None
    await db.delete(obj)
    await db.flush()
    return obj
