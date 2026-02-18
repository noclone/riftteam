import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils import create_link_view, format_api_error, get_api_secret, get_session, parse_riot_id

log = logging.getLogger("riftteam.register")


class RegisterCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-profil-create", description="Crée ton profil RiftTeam à partir de ton Riot ID")
    @app_commands.describe(riot_id="Ton Riot ID (ex: Pseudo#TAG)")
    async def rt_register(self, interaction: discord.Interaction, riot_id: str) -> None:
        parsed = parse_riot_id(riot_id)
        if not parsed:
            await interaction.response.send_message(
                "Format invalide. Utilise `Pseudo#TAG` (ex: `noclone67#EUW`).",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        name, tag = parsed
        slug = f"{name}-{tag}"
        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)

        try:
            async with session.get(f"/api/players/by-discord/{interaction.user.id}") as resp:
                if resp.status == 200:
                    existing = await resp.json()
                    existing_name = f"{existing['riot_game_name']}#{existing['riot_tag_line']}"
                    await interaction.followup.send(
                        f"Tu as déjà un profil (**{existing_name}**). Utilise `/rt-profil-edit` pour le modifier.",
                    )
                    return
        except discord.NotFound:
            raise
        except Exception as exc:
            log.exception("Failed to check existing profile by discord ID")
            await interaction.followup.send(format_api_error(exc))
            return

        try:
            async with session.get(f"/api/riot/check/{name}/{tag}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        f"Riot ID **{riot_id}** introuvable. Vérifie l'orthographe et le tag.",
                    )
                    return
                resp.raise_for_status()
        except discord.NotFound:
            raise
        except Exception as exc:
            log.exception("Failed to check Riot ID %s", riot_id)
            await interaction.followup.send(format_api_error(exc))
            return

        try:
            async with session.get(f"/api/players/{slug}") as resp:
                if resp.status == 200:
                    existing_player = await resp.json()
                    if existing_player.get("discord_user_id") is not None:
                        await interaction.followup.send(
                            f"Un profil existe déjà pour **{riot_id}** et est déjà attribué.",
                        )
                        return
        except Exception as exc:
            log.exception("Failed to check existing player %s", slug)
            await interaction.followup.send(format_api_error(exc))
            return

        try:
            payload = {
                "action": "create",
                "discord_user_id": str(interaction.user.id),
                "discord_username": interaction.user.name,
                "game_name": name,
                "tag_line": tag,
            }
            async with session.post(
                "/api/tokens",
                json=payload,
                headers={"X-Bot-Secret": api_secret},
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                url = data["url"]
        except Exception as exc:
            log.exception("Failed to create token")
            await interaction.followup.send(format_api_error(exc))
            return

        view = create_link_view("Créer mon profil", url)
        await interaction.followup.send(
            f"Clique ci-dessous pour créer ton profil **{riot_id}** !\n"
            f"Le lien expire dans 30 minutes.",
            view=view,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RegisterCog(bot))
