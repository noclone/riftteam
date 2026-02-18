import discord
from discord import app_commands
from discord.ext import commands


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-help", description="Liste toutes les commandes RiftTeam")
    async def rt_help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Commandes RiftTeam",
            description="Toutes les commandes commencent par `/rt-`",
            color=0x5865F2,
        )

        embed.add_field(
            name="\U0001f464 Profil",
            value=(
                "`/rt-profil-create` — Crée ton profil\n"
                "`/rt-profil-show` — Affiche un profil\n"
                "`/rt-profil-edit` — Modifie ton profil\n"
                "`/rt-profil-post` — Partage ton profil dans le channel"
            ),
            inline=False,
        )

        embed.add_field(
            name="\U0001f6e1\ufe0f \u00c9quipe",
            value=(
                "`/rt-team-create` — Crée une équipe\n"
                "`/rt-team-edit` — Modifie ton équipe\n"
                "`/rt-team-roster add` — Ajoute un joueur\n"
                "`/rt-team-roster remove` — Retire un joueur\n"
                "`/rt-post-team` — Partage ton équipe dans le channel"
            ),
            inline=False,
        )

        embed.add_field(
            name="\U0001f50d Recherche",
            value=(
                "`/rt-lfp` — Joueurs dispo (filtre r\u00f4le, rang)\n"
                "`/rt-lft` — \u00c9quipes dispo (filtre r\u00f4le, rang)\n"
                "`/rt-apply` — Postule \u00e0 une \u00e9quipe\n"
                "`/rt-recruit` — Recrute un joueur"
            ),
            inline=False,
        )

        embed.add_field(
            name="\u2694\ufe0f Scrims",
            value=(
                "`/rt-scrim-post` — Poste un scrim\n"
                "`/rt-scrim-search` — Cherche des scrims (date, heure, format, rang)\n"
                "`/rt-scrim-cancel` — Annule le scrim actif de ton équipe"
            ),
            inline=False,
        )

        embed.add_field(
            name="\u2699\ufe0f Autre",
            value=(
                "`/rt-reactivate` — R\u00e9active profil / \u00e9quipe\n"
                "`/rt-setup` — Channel d'annonces *(admin)*"
            ),
            inline=False,
        )

        embed.set_footer(text="RiftTeam \u00b7 riftteam.gg")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
