import logging

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("riftteam.register")


class RegisterCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="register", description="Crée ton profil RiftTeam à partir de ton Riot ID")
    @app_commands.describe(riot_id="Ton Riot ID (ex: Pseudo#TAG)")
    async def register(self, interaction: discord.Interaction, riot_id: str) -> None:
        parts = riot_id.split("#", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            await interaction.response.send_message(
                "Format invalide. Utilise `Pseudo#TAG` (ex: `noclone67#EUW`).",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        name, tag = parts
        slug = f"{name}-{tag}"
        session = self.bot.http_session  # type: ignore[attr-defined]
        api_secret = self.bot.api_secret  # type: ignore[attr-defined]

        try:
            async with session.get(f"/api/players/by-discord/{interaction.user.id}") as resp:
                if resp.status == 200:
                    existing = await resp.json()
                    existing_name = f"{existing['riot_game_name']}#{existing['riot_tag_line']}"
                    await interaction.followup.send(
                        f"Tu as déjà un profil (**{existing_name}**). Utilise `/edit` pour le modifier.",
                    )
                    return
        except Exception:
            log.exception("Failed to check existing profile by discord ID")
            await interaction.followup.send(
                "Erreur lors de la vérification. Réessaie plus tard.",
            )
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
        except Exception:
            log.exception("Failed to check Riot ID %s", riot_id)
            await interaction.followup.send("Erreur lors de la vérification du Riot ID.")
            return

        try:
            async with session.get(f"/api/players/{slug}") as resp:
                if resp.status == 200:
                    await interaction.followup.send(
                        f"Un profil existe déjà pour **{riot_id}**. "
                        f"Si c'est le tien, utilise `/edit`.",
                    )
                    return
        except Exception:
            log.exception("Failed to check existing player %s", slug)
            await interaction.followup.send("Erreur lors de la vérification.")
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
        except Exception:
            log.exception("Failed to create token")
            await interaction.followup.send("Erreur lors de la création du lien.")
            return

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Créer mon profil",
            style=discord.ButtonStyle.link,
            url=url,
        ))
        await interaction.followup.send(
            f"Clique ci-dessous pour créer ton profil **{riot_id}** !\n"
            f"Le lien expire dans 30 minutes.",
            view=view,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RegisterCog(bot))
