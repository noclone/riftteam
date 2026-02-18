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
BOT_API_SECRET = os.getenv("BOT_API_SECRET", "change-bot-secret-in-production")
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("riftteam")

COGS = ["cogs.profile", "cogs.lfp", "cogs.admin", "cogs.register", "cogs.edit", "cogs.team", "cogs.reactivate", "cogs.matchmaking", "cogs.scrim", "cogs.help"]

DEACTIVATION_INTERVAL = 12 * 3600


class RiftBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.http_session: aiohttp.ClientSession | None = None
        self.api_secret: str = BOT_API_SECRET
        self._deactivation_task: asyncio.Task | None = None

    async def setup_hook(self) -> None:
        self.http_session = aiohttp.ClientSession(
            base_url=API_URL,
            headers={"X-Bot-Secret": BOT_API_SECRET},
        )
        for cog in COGS:
            await self.load_extension(cog)
            log.info("Loaded %s", cog)

    async def on_ready(self) -> None:
        assert self.user is not None
        if DEV_GUILD_ID:
            guild = discord.Object(id=int(DEV_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()
        log.info("Logged in as %s — synced %d commands", self.user, len(synced))
        if self._deactivation_task is None:
            self._deactivation_task = asyncio.create_task(self._deactivation_loop())

    async def _deactivation_loop(self) -> None:
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                await self._run_deactivation()
            except Exception:
                log.exception("Deactivation loop error")
            await asyncio.sleep(DEACTIVATION_INTERVAL)

    async def _run_deactivation(self) -> None:
        if not self.http_session:
            return
        try:
            async with self.http_session.post(
                "/api/maintenance/deactivate-inactive",
                headers={"X-Bot-Secret": self.api_secret},
            ) as resp:
                if resp.status != 200:
                    log.warning("Deactivation endpoint returned %d", resp.status)
                    return
                data = await resp.json()
        except Exception:
            log.exception("Failed to call deactivation endpoint")
            return

        for discord_id in data.get("players", []):
            await self._send_deactivation_dm(
                discord_id, f"rt_reactivate_player:{discord_id}",
                "Ton profil LFT a été désactivé pour inactivité (14 jours sans mise à jour). "
                "Utilise `/rt-reactivate` pour le réactiver, ou clique directement sur le bouton ci-dessous.",
            )

        for discord_id in data.get("teams", []):
            await self._send_deactivation_dm(
                discord_id, f"rt_reactivate_team:{discord_id}",
                "Ton équipe a été désactivée pour inactivité (14 jours sans mise à jour). "
                "Utilise `/rt-reactivate` pour la réactiver, ou clique directement sur le bouton ci-dessous.",
            )

    async def _send_deactivation_dm(self, discord_id: str, custom_id: str, message: str) -> None:
        try:
            user = await self.fetch_user(int(discord_id))
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(
                label="Réactiver",
                style=discord.ButtonStyle.success,
                custom_id=custom_id,
            ))
            await user.send(message, view=view)
        except Exception:
            log.warning("Failed to DM user %s", discord_id)

    async def close(self) -> None:
        if self._deactivation_task:
            self._deactivation_task.cancel()
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
