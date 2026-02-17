import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("riftteam")

COGS = ["cogs.profile", "cogs.lft", "cogs.admin"]


class RiftBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.http_session: aiohttp.ClientSession | None = None

    async def setup_hook(self) -> None:
        self.http_session = aiohttp.ClientSession(base_url=API_URL)
        for cog in COGS:
            await self.load_extension(cog)
            log.info("Loaded %s", cog)

    async def on_ready(self) -> None:
        assert self.user is not None
        synced = await self.tree.sync()
        log.info("Logged in as %s — synced %d commands", self.user, len(synced))

    async def close(self) -> None:
        if self.http_session:
            await self.http_session.close()
        await super().close()


async def main() -> None:
    if not TOKEN:
        log.error("DISCORD_BOT_TOKEN is not set")
        sys.exit(1)

    bot = RiftBot()
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
