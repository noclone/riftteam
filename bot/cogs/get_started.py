import discord
from discord import app_commands
from discord.ext import commands


CHOICE_PLAYER = "player"
CHOICE_TEAM = "team"


def _player_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Démarrer en tant que joueur",
        description="Suis ces étapes pour créer ton profil et trouver une équipe.",
        color=0x5865F2,
    )
    embed.add_field(
        name="Étape 1",
        value="`/rt-profil-create Pseudo#TAG` — Crée ton profil",
        inline=False,
    )
    embed.add_field(
        name="Étape 2",
        value="`/rt-profil-enable-lft` — Active le mode LFT pour être visible des équipes",
        inline=False,
    )
    embed.add_field(
        name="Étape 3",
        value="`/rt-lft` — Parcours les équipes qui recrutent",
        inline=False,
    )
    embed.add_field(
        name="\u200b",
        value="Pour toute modification du profil : `/rt-profil-edit`",
        inline=False,
    )
    return embed


def _team_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Démarrer en tant qu'équipe",
        description="Suis ces étapes pour créer ton équipe et recruter des joueurs.",
        color=0xE67E22,
    )
    embed.add_field(
        name="Étape 1",
        value="`/rt-team-create NomEquipe` — Crée ton équipe",
        inline=False,
    )
    embed.add_field(
        name="Étape 2",
        value="`/rt-team-enable-lfp` — Active le mode LFP pour être visible des joueurs",
        inline=False,
    )
    embed.add_field(
        name="Étape 3",
        value="`/rt-lfp` — Parcours les joueurs disponibles",
        inline=False,
    )
    embed.add_field(
        name="\u200b",
        value="Pour modifier le roster : `/rt-team-roster add` · `/rt-team-roster remove`\nPour modifier l'équipe : `/rt-team-edit`",
        inline=False,
    )
    return embed


class GetStartedCog(commands.Cog):
    """Slash command showing onboarding steps for players or teams."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-get-started", description="Comment démarrer sur RiftTeam")
    @app_commands.describe(choice="Tu cherches une équipe ou tu recrutes ?")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Joueur — Je cherche une équipe", value=CHOICE_PLAYER),
        app_commands.Choice(name="Équipe — Je recrute des joueurs", value=CHOICE_TEAM),
    ])
    async def rt_get_started(
        self,
        interaction: discord.Interaction,
        choice: app_commands.Choice[str],
    ) -> None:
        if choice.value == CHOICE_TEAM:
            embed = _team_embed()
        else:
            embed = _player_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GetStartedCog(bot))
