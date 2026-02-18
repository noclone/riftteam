import asyncio
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import players, riot, scrims, teams, tokens
from app.routers.og import router as og_router
from app.services.sync import deactivate_inactive, sync_active_ranks
from shared.riot_client import RiotClient

logger = logging.getLogger("riftteam")

SYNC_INTERVAL = 12 * 3600


async def _rank_sync_loop(app: FastAPI) -> None:
    while True:
        try:
            await sync_active_ranks(client=app.state.riot_client)
        except Exception:
            logger.exception("Rank sync loop error")
        await asyncio.sleep(SYNC_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.riot_api_key:
        app.state.riot_client = RiotClient(settings.riot_api_key)
    else:
        app.state.riot_client = None
    task = asyncio.create_task(_rank_sync_loop(app))
    yield
    task.cancel()


app = FastAPI(title="RiftTeam API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(scrims.router, prefix="/api")
app.include_router(riot.router, prefix="/api")
app.include_router(tokens.router, prefix="/api")
app.include_router(og_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/maintenance/deactivate-inactive")
async def maintenance_deactivate(x_bot_secret: str = Header(...)):
    if x_bot_secret != settings.bot_api_secret:
        raise HTTPException(403, "Invalid bot secret")
    result = await deactivate_inactive()
    return result
