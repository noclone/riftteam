import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from cogs.profile import build_profile_embed
from shared.constants import RANK_COLORS, RANK_ORDER, ROLE_EMOJIS, ROLE_NAMES

APP_URL = os.getenv("APP_URL", "http://localhost:5173")

log = logging.getLogger("riftteam.matchmaking")

RANK_ICON_BASE = "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests"

ACTIVITY_LABELS: dict[str, str] = {
    "SCRIMS": "Scrims",
    "TOURNOIS": "Tournois",
    "LAN": "LAN",
    "FLEX": "Flex",
    "CLASH": "Clash",
}

AMBIANCE_LABELS: dict[str, str] = {
    "FUN": "For fun",
    "TRYHARD": "Tryhard",
}


def _rank_short(tier: str | None, division: str | None) -> str:
    if not tier:
        return "Unranked"
    t = tier.capitalize()
    if division and tier.upper() not in ("MASTER", "GRANDMASTER", "CHALLENGER"):
        return f"{t} {division}"
    return t


def _rank_in_range(player_tier: str | None, min_rank: str | None, max_rank: str | None) -> bool:
    if not min_rank and not max_rank:
        return True
    if not player_tier:
        return False
    player_order = RANK_ORDER.get(player_tier.upper())
    if player_order is None:
        return True
    if min_rank:
        min_order = RANK_ORDER.get(min_rank.upper())
        if min_order is not None and player_order < min_order:
            return False
    if max_rank:
        max_order = RANK_ORDER.get(max_rank.upper())
        if max_order is not None and player_order > max_order:
            return False
    return True


def _role_matches(player: dict, wanted_roles: list[str] | None) -> bool:
    if not wanted_roles:
        return True
    primary = player.get("primary_role")
    secondary = player.get("secondary_role")
    player_roles = {r for r in [primary, secondary] if r}
    if not player_roles:
        return True
    return bool(player_roles & set(wanted_roles))


def _pick_role(player: dict, wanted_roles: list[str] | None) -> str:
    primary = player.get("primary_role")
    secondary = player.get("secondary_role")
    if wanted_roles:
        if primary and primary in wanted_roles:
            return primary
        if secondary and secondary in wanted_roles:
            return secondary
    return primary or "MIDDLE"


def _format_rank(tier: str | None) -> str:
    return tier.capitalize() if tier else "Unranked"


def _format_roles(player: dict) -> str:
    primary = player.get("primary_role")
    secondary = player.get("secondary_role")
    roles = [r for r in [primary, secondary] if r]
    if not roles:
        return "inconnu"
    return " / ".join(ROLE_NAMES.get(r, r) for r in roles)


def _format_wanted(wanted_roles: list[str]) -> str:
    return ", ".join(ROLE_NAMES.get(r, r) for r in wanted_roles)


def _format_rank_range(min_rank: str | None, max_rank: str | None) -> str:
    parts = []
    if min_rank:
        parts.append(min_rank.capitalize())
    if max_rank:
        parts.append(max_rank.capitalize())
    return " → ".join(parts)


def build_team_embed(team: dict) -> discord.Embed:
    min_rank = team.get("min_rank")
    max_rank = team.get("max_rank")
    tier = min_rank or max_rank
    color = RANK_COLORS.get(tier.upper(), 0xE67E22) if tier else 0xE67E22

    url = f"{APP_URL}/t/{team['slug']}"
    embed = discord.Embed(title=team["name"], url=url, color=color)

    wanted = team.get("wanted_roles") or []
    if wanted:
        wanted_str = ", ".join(f"{ROLE_EMOJIS.get(r, '')} {ROLE_NAMES.get(r, r)}" for r in wanted)
        embed.add_field(name="Rôles recherchés", value=wanted_str, inline=False)

    if min_rank or max_rank:
        embed.add_field(name="Elo", value=_format_rank_range(min_rank, max_rank), inline=True)

    members = team.get("members", [])
    if members:
        roster_lines = []
        for m in members:
            p = m["player"]
            role_emoji = ROLE_EMOJIS.get(m["role"], "")
            rank = _rank_short(p.get("rank_solo_tier"), p.get("rank_solo_division"))
            roster_lines.append(f"{role_emoji} **{p['riot_game_name']}**#{p['riot_tag_line']} — {rank}")
        embed.add_field(name=f"Roster ({len(members)}/5)", value="\n".join(roster_lines), inline=False)

    activities = team.get("activities") or []
    ambiance_val = team.get("ambiance")
    freq_min = team.get("frequency_min")
    freq_max = team.get("frequency_max")
    info_parts: list[str] = []
    if activities:
        labels = [ACTIVITY_LABELS.get(a, a) for a in activities]
        info_parts.append(", ".join(labels))
    if ambiance_val:
        info_parts.append(AMBIANCE_LABELS.get(ambiance_val, ambiance_val))
    if freq_min is not None and freq_max is not None:
        info_parts.append(f"{freq_min}-{freq_max}x / semaine")
    if info_parts:
        embed.add_field(name="Info", value=" · ".join(info_parts), inline=False)

    description = team.get("description")
    if description:
        truncated = description[:150] + "…" if len(description) > 150 else description
        embed.add_field(name="Description", value=truncated, inline=False)

    if tier:
        embed.set_thumbnail(url=f"{RANK_ICON_BASE}/{tier.lower()}.png")

    embed.set_footer(text="RiftTeam")
    return embed


class MatchmakingCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _do_apply(self, interaction: discord.Interaction, team_slug: str) -> None:
        """Core apply logic. Interaction must already be deferred (ephemeral)."""
        session = self.bot.http_session  # type: ignore[attr-defined]

        try:
            async with session.get(f"/api/players/by-discord/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        "Tu n'as pas de profil RiftTeam. Utilise `/rt-profil-create Pseudo#TAG` pour en créer un.",
                        ephemeral=True,
                    )
                    return
                resp.raise_for_status()
                player = await resp.json()
        except Exception:
            log.exception("Failed to fetch player profile")
            await interaction.followup.send("Erreur lors de la récupération de ton profil.", ephemeral=True)
            return

        try:
            async with session.get(f"/api/teams/{team_slug}") as resp:
                if resp.status == 404:
                    await interaction.followup.send("Équipe introuvable.", ephemeral=True)
                    return
                resp.raise_for_status()
                team = await resp.json()
        except Exception:
            log.exception("Failed to fetch team %s", team_slug)
            await interaction.followup.send("Erreur lors de la récupération de l'équipe.", ephemeral=True)
            return

        if str(interaction.user.id) == team.get("captain_discord_id"):
            await interaction.followup.send("Tu ne peux pas postuler à ta propre équipe.", ephemeral=True)
            return

        if not team.get("is_lfp"):
            await interaction.followup.send(
                f"L'équipe **{team['name']}** ne cherche pas de joueurs actuellement.",
                ephemeral=True,
            )
            return

        member_ids = {m["player"]["id"] for m in team.get("members", [])}
        if player["id"] in member_ids:
            await interaction.followup.send(
                f"Tu fais déjà partie de l'équipe **{team['name']}**.",
                ephemeral=True,
            )
            return

        wanted_roles = team.get("wanted_roles")
        if not _role_matches(player, wanted_roles):
            await interaction.followup.send(
                f"Ton rôle ({_format_roles(player)}) ne correspond pas aux rôles recherchés ({_format_wanted(wanted_roles)}).",
                ephemeral=True,
            )
            return

        if not _rank_in_range(player.get("rank_solo_tier"), team.get("min_rank"), team.get("max_rank")):
            player_rank = _format_rank(player.get("rank_solo_tier"))
            range_str = _format_rank_range(team.get("min_rank"), team.get("max_rank"))
            await interaction.followup.send(
                f"Ton elo ({player_rank}) ne correspond pas à la fourchette de l'équipe ({range_str}).",
                ephemeral=True,
            )
            return

        captain_id = team.get("captain_discord_id")
        try:
            captain = await self.bot.fetch_user(int(captain_id))
            embed = build_profile_embed(player)
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(
                label="Contacter",
                style=discord.ButtonStyle.secondary,
                custom_id=f"rt_contact:{interaction.user.id}",
            ))
            view.add_item(discord.ui.Button(
                label="Voir le profil",
                style=discord.ButtonStyle.link,
                url=f"{APP_URL}/p/{player['slug']}",
            ))
            await captain.send(
                f"**{player['riot_game_name']}#{player['riot_tag_line']}** souhaite rejoindre ton équipe "
                f"**{team['name']}** !",
                embed=embed,
                view=view,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                f"Impossible d'envoyer un DM au capitaine de **{team['name']}**. "
                f"Il a peut-être désactivé les DMs.",
                ephemeral=True,
            )
            return
        except Exception:
            log.exception("Failed to DM captain %s", captain_id)
            await interaction.followup.send("Erreur lors de l'envoi de la candidature.", ephemeral=True)
            return

        await interaction.followup.send(
            f"Candidature envoyée à l'équipe **{team['name']}** !",
            ephemeral=True,
        )

    async def _do_recruit(self, interaction: discord.Interaction, player_slug: str) -> None:
        """Core recruit logic. Interaction must already be deferred (ephemeral)."""
        session = self.bot.http_session  # type: ignore[attr-defined]

        try:
            async with session.get(f"/api/teams/by-captain/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        "Tu n'as pas d'équipe. Utilise `/rt-team-create NomEquipe` pour en créer une !",
                        ephemeral=True,
                    )
                    return
                resp.raise_for_status()
                team = await resp.json()
        except Exception:
            log.exception("Failed to fetch team")
            await interaction.followup.send("Erreur lors de la récupération de ton équipe.", ephemeral=True)
            return

        try:
            async with session.get(f"/api/players/{player_slug}") as resp:
                if resp.status == 404:
                    await interaction.followup.send("Profil introuvable.", ephemeral=True)
                    return
                resp.raise_for_status()
                player = await resp.json()
        except Exception:
            log.exception("Failed to fetch player %s", player_slug)
            await interaction.followup.send("Erreur lors de la récupération du profil.", ephemeral=True)
            return

        riot_id = f"{player['riot_game_name']}#{player['riot_tag_line']}"

        if str(interaction.user.id) == player.get("discord_user_id"):
            await interaction.followup.send("Tu ne peux pas te recruter toi-même.", ephemeral=True)
            return

        if not player.get("is_lft"):
            await interaction.followup.send(
                f"**{riot_id}** ne cherche pas d'équipe actuellement.",
                ephemeral=True,
            )
            return

        player_discord_id = player.get("discord_user_id")
        if not player_discord_id:
            await interaction.followup.send(
                f"**{riot_id}** n'a pas de compte Discord lié. Impossible de le contacter.",
                ephemeral=True,
            )
            return

        member_ids = {m["player"]["id"] for m in team.get("members", [])}
        if player["id"] in member_ids:
            await interaction.followup.send(
                f"**{riot_id}** fait déjà partie de ton équipe.",
                ephemeral=True,
            )
            return

        wanted_roles = team.get("wanted_roles")
        if not _role_matches(player, wanted_roles):
            await interaction.followup.send(
                f"Le rôle de **{riot_id}** ({_format_roles(player)}) ne correspond pas "
                f"aux rôles recherchés par ton équipe ({_format_wanted(wanted_roles)}).",
                ephemeral=True,
            )
            return

        if not _rank_in_range(player.get("rank_solo_tier"), team.get("min_rank"), team.get("max_rank")):
            player_rank = _format_rank(player.get("rank_solo_tier"))
            range_str = _format_rank_range(team.get("min_rank"), team.get("max_rank"))
            await interaction.followup.send(
                f"L'elo de **{riot_id}** ({player_rank}) ne correspond pas "
                f"à la fourchette de ton équipe ({range_str}).",
                ephemeral=True,
            )
            return

        try:
            target_user = await self.bot.fetch_user(int(player_discord_id))
            embed = build_team_embed(team)
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(
                label="Contacter",
                style=discord.ButtonStyle.secondary,
                custom_id=f"rt_contact:{interaction.user.id}",
            ))
            view.add_item(discord.ui.Button(
                label="Voir l'équipe",
                style=discord.ButtonStyle.link,
                url=f"{APP_URL}/t/{team['slug']}",
            ))
            await target_user.send(
                f"L'équipe **{team['name']}** souhaite te recruter !",
                embed=embed,
                view=view,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                f"Impossible d'envoyer un DM à **{riot_id}**. "
                f"Le joueur a peut-être désactivé les DMs.",
                ephemeral=True,
            )
            return
        except Exception:
            log.exception("Failed to DM player %s", player_discord_id)
            await interaction.followup.send("Erreur lors de l'envoi de la proposition.", ephemeral=True)
            return

        await interaction.followup.send(
            f"Proposition de recrutement envoyée à **{riot_id}** !",
            ephemeral=True,
        )

    @app_commands.command(name="rt-apply", description="Postule à une équipe LFP")
    @app_commands.describe(team_name="Nom de l'équipe")
    async def rt_apply(self, interaction: discord.Interaction, team_name: str) -> None:
        await interaction.response.defer(ephemeral=True)
        slug = team_name.lower().replace(" ", "-")
        await self._do_apply(interaction, slug)

    @app_commands.command(name="rt-recruit", description="Recrute un joueur pour ton équipe")
    @app_commands.describe(riot_id="Riot ID du joueur (ex: Pseudo#TAG)")
    async def rt_recruit(self, interaction: discord.Interaction, riot_id: str) -> None:
        parts = riot_id.split("#", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            await interaction.response.send_message(
                "Format invalide. Utilise `Pseudo#TAG`.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        name, tag = parts
        slug = f"{name}-{tag}"
        await self._do_recruit(interaction, slug)

    @app_commands.command(name="rt-profil-post", description="Poste ton profil dans le channel")
    async def rt_post_profil(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        session = self.bot.http_session  # type: ignore[attr-defined]

        try:
            async with session.get(f"/api/players/by-discord/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        "Tu n'as pas de profil RiftTeam. Utilise `/rt-profil-create Pseudo#TAG` pour en créer un.",
                        ephemeral=True,
                    )
                    return
                resp.raise_for_status()
                player = await resp.json()
        except Exception:
            log.exception("Failed to fetch player profile")
            await interaction.followup.send("Erreur lors de la récupération de ton profil.", ephemeral=True)
            return

        embed = build_profile_embed(player)
        view = discord.ui.View(timeout=None)
        discord_user_id = player.get("discord_user_id")
        if discord_user_id:
            view.add_item(discord.ui.Button(
                label="Contacter",
                style=discord.ButtonStyle.secondary,
                custom_id=f"rt_contact:{discord_user_id}",
            ))
        view.add_item(discord.ui.Button(
            label="Voir le profil",
            style=discord.ButtonStyle.link,
            url=f"{APP_URL}/p/{player['slug']}",
        ))

        await interaction.channel.send(embed=embed, view=view)  # type: ignore[union-attr]
        await interaction.delete_original_response()

    @app_commands.command(name="rt-post-team", description="Poste ton équipe dans le channel")
    async def rt_post_team(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        session = self.bot.http_session  # type: ignore[attr-defined]

        try:
            async with session.get(f"/api/teams/by-captain/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        "Tu n'as pas d'équipe. Utilise `/rt-team-create NomEquipe` pour en créer une !",
                        ephemeral=True,
                    )
                    return
                resp.raise_for_status()
                team = await resp.json()
        except Exception:
            log.exception("Failed to fetch team")
            await interaction.followup.send("Erreur lors de la récupération de ton équipe.", ephemeral=True)
            return

        embed = build_team_embed(team)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Postuler",
            style=discord.ButtonStyle.primary,
            custom_id=f"rt_apply_btn:{team['slug']}",
        ))
        view.add_item(discord.ui.Button(
            label="Voir l'équipe",
            style=discord.ButtonStyle.link,
            url=f"{APP_URL}/t/{team['slug']}",
        ))

        await interaction.channel.send(embed=embed, view=view)  # type: ignore[union-attr]
        await interaction.delete_original_response()

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")  # type: ignore[union-attr]
        if custom_id.startswith("rt_contact:"):
            target_id = custom_id[len("rt_contact:"):]
            if str(interaction.user.id) == target_id:
                await interaction.response.send_message("C'est ton propre profil !", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"Envoie un DM à <@{target_id}> pour le contacter !",
                    ephemeral=True,
                )
        elif custom_id.startswith("rt_apply_btn:"):
            await interaction.response.defer(ephemeral=True)
            await self._do_apply(interaction, custom_id[len("rt_apply_btn:"):])

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MatchmakingCog(bot))
