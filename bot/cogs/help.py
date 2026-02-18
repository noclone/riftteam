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
            color=0x5865F2,
        )

        embed.add_field(
            name="Profil joueur",
            value=(
                "`/rt-register <Pseudo#TAG>` — Crée ton profil\n"
                "`/rt-edit` — Modifie ton profil (lien vers le site)\n"
                "`/rt-profil <Pseudo#TAG>` — Affiche le profil d'un joueur\n"
                "`/rt-reactivate` — Réactive ton profil / équipe désactivés"
            ),
            inline=False,
        )

        embed.add_field(
            name="Recherche",
            value=(
                "`/rt-lfp [role] [min_rank] [max_rank]` — Joueurs qui cherchent une équipe\n"
                "`/rt-lft [role] [min_rank] [max_rank]` — Équipes qui cherchent des joueurs\n"
                "`/rt-apply <nom_équipe>` — Postule à une équipe (DM avec boutons accepter/refuser)\n"
                "`/rt-recruit <Pseudo#TAG>` — Recrute un joueur pour ton équipe (DM avec boutons accepter/refuser)\n"
                "`/rt-post-profil` — Poste ton profil dans le channel (bouton Recruter)\n"
                "`/rt-post-team` — Poste ton équipe dans le channel (bouton Postuler)"
            ),
            inline=False,
        )

        embed.add_field(
            name="Équipe",
            value=(
                "`/rt-team-create <nom>` — Crée une équipe\n"
                "`/rt-team-edit` — Modifie ton équipe (lien vers le site)\n"
                "`/rt-team-roster add <Pseudo#TAG> <role>` — Ajoute un joueur au roster\n"
                "`/rt-team-roster remove <Pseudo#TAG>` — Retire un joueur du roster"
            ),
            inline=False,
        )

        embed.add_field(
            name="Admin",
            value="`/rt-setup` — Configure le channel d'annonces (manage_guild)",
            inline=False,
        )

        embed.set_footer(text="RiftTeam · riftteam.gg")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
