import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import APP_URL
from constants import RANK_CHOICES, ROLE_CHOICES
from shared.constants import RANK_COLORS, ROLE_EMOJIS, ROLE_NAMES
from shared.format import format_rank
from utils import build_info_parts, build_nav_view, build_no_results_msg, create_link_view, decode_list_filters, encode_list_filters, format_api_error, get_api_secret, get_session, parse_riot_id

log = logging.getLogger("riftteam.team")

PAGE_SIZE = 5


class TeamCog(commands.Cog):
    """Slash commands for team CRUD, roster management and LFT team browsing."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rt-team-create", description="Crée une équipe RiftTeam")
    @app_commands.describe(name="Nom de l'équipe")
    async def rt_team_create(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer(ephemeral=True)

        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)

        try:
            async with session.get(f"/api/teams/by-captain/{interaction.user.id}") as resp:
                if resp.status == 200:
                    existing = await resp.json()
                    await interaction.followup.send(
                        f"Tu es déjà capitaine de **{existing['name']}**. "
                        f"Utilise `/rt-team-edit` pour la modifier.",
                    )
                    return
        except Exception as exc:
            log.exception("Failed to check existing team")
            await interaction.followup.send(format_api_error(exc))
            return

        try:
            payload = {
                "action": "team_create",
                "discord_user_id": str(interaction.user.id),
                "discord_username": interaction.user.name,
                "team_name": name,
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
            log.exception("Failed to create team token")
            await interaction.followup.send(format_api_error(exc))
            return

        view = create_link_view("Créer mon équipe", url)
        await interaction.followup.send(
            f"Clique ci-dessous pour créer ton équipe **{name}** !\n"
            f"Le lien expire dans 30 minutes.",
            view=view,
        )

    @app_commands.command(name="rt-team-edit", description="Modifie ton équipe RiftTeam")
    async def rt_team_edit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)

        try:
            async with session.get(f"/api/teams/by-captain/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        "Tu n'as pas d'équipe. Utilise `/rt-team-create NomEquipe` pour en créer une !",
                    )
                    return
                resp.raise_for_status()
                team = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch team by captain")
            await interaction.followup.send(format_api_error(exc))
            return

        try:
            payload = {
                "action": "team_edit",
                "discord_user_id": str(interaction.user.id),
                "discord_username": interaction.user.name,
                "slug": team["slug"],
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
            log.exception("Failed to create team edit token")
            await interaction.followup.send(format_api_error(exc))
            return

        view = create_link_view("Modifier mon équipe", url)
        await interaction.followup.send(
            f"Clique ci-dessous pour modifier ton équipe **{team['name']}** !\n"
            f"Le lien expire dans 30 minutes.",
            view=view,
        )

    team_roster_group = app_commands.Group(name="rt-team-roster", description="Gérer le roster de ton équipe")

    @team_roster_group.command(name="add", description="Ajouter un joueur au roster")
    @app_commands.describe(riot_id="Riot ID du joueur (ex: Pseudo#TAG)", role="Rôle assigné")
    @app_commands.choices(role=ROLE_CHOICES)
    async def roster_add(
        self,
        interaction: discord.Interaction,
        riot_id: str,
        role: app_commands.Choice[str],
    ) -> None:
        parsed = parse_riot_id(riot_id)
        if not parsed:
            await interaction.response.send_message(
                "Format invalide. Utilise `Pseudo#TAG`.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)

        try:
            async with session.get(f"/api/teams/by-captain/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send("Tu n'as pas d'équipe.")
                    return
                resp.raise_for_status()
                team = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch team")
            await interaction.followup.send(format_api_error(exc))
            return

        name, tag = parsed
        player_slug = f"{name}-{tag}"

        try:
            payload = {
                "player_slug": player_slug,
                "role": role.value,
                "discord_user_id": str(interaction.user.id),
            }
            async with session.post(
                f"/api/teams/{team['slug']}/members",
                json=payload,
                headers={"X-Bot-Secret": api_secret},
            ) as resp:
                if resp.status == 404:
                    await interaction.followup.send(f"Riot ID **{riot_id}** introuvable.")
                    return
                if resp.status == 409:
                    body = await resp.json()
                    await interaction.followup.send(body.get("detail", "Ce joueur est déjà dans une équipe."))
                    return
                if resp.status in (502, 503):
                    body = await resp.json()
                    detail = body.get("detail", "Erreur Riot API")
                    await interaction.followup.send(f"Impossible de récupérer les données Riot : {detail}")
                    return
                resp.raise_for_status()
        except discord.NotFound:
            raise
        except Exception as exc:
            log.exception("Failed to add member")
            await interaction.followup.send(format_api_error(exc))
            return

        await interaction.followup.send(
            f"**{riot_id}** ajouté au roster en tant que **{role.name}** !",
        )

    @team_roster_group.command(name="remove", description="Retirer un joueur du roster")
    @app_commands.describe(riot_id="Riot ID du joueur (ex: Pseudo#TAG)")
    async def roster_remove(self, interaction: discord.Interaction, riot_id: str) -> None:
        parsed = parse_riot_id(riot_id)
        if not parsed:
            await interaction.response.send_message(
                "Format invalide. Utilise `Pseudo#TAG`.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        session = get_session(self.bot)
        api_secret = get_api_secret(self.bot)

        try:
            async with session.get(f"/api/teams/by-captain/{interaction.user.id}") as resp:
                if resp.status == 404:
                    await interaction.followup.send("Tu n'as pas d'équipe.")
                    return
                resp.raise_for_status()
                team = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch team")
            await interaction.followup.send(format_api_error(exc))
            return

        name, tag = parsed
        player_slug = f"{name}-{tag}"

        try:
            async with session.delete(
                f"/api/teams/{team['slug']}/members/{player_slug}",
                params={"discord_user_id": str(interaction.user.id)},
                headers={"X-Bot-Secret": api_secret},
            ) as resp:
                if resp.status == 404:
                    await interaction.followup.send(f"**{riot_id}** n'est pas dans ton équipe.")
                    return
                resp.raise_for_status()
        except discord.NotFound:
            raise
        except Exception as exc:
            log.exception("Failed to remove member")
            await interaction.followup.send(format_api_error(exc))
            return

        await interaction.followup.send(f"**{riot_id}** retiré du roster.")

    async def _fetch_lft_and_respond(
        self,
        interaction: discord.Interaction,
        page: int,
        role: str | None,
        min_rank: str | None,
        max_rank: str | None,
        *,
        edit: bool = False,
    ) -> None:
        """Fetch a page of LFP teams from the API and send/edit the response."""
        params: dict[str, str] = {
            "is_lfp": "true",
            "limit": str(PAGE_SIZE),
            "offset": str(page * PAGE_SIZE),
        }
        if role:
            params["role"] = role
        if min_rank:
            params["min_rank"] = min_rank
        if max_rank:
            params["max_rank"] = max_rank

        session = get_session(self.bot)
        try:
            async with session.get("/api/teams", params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception as exc:
            log.exception("Failed to fetch LFT teams")
            msg = format_api_error(exc)
            if edit:
                await interaction.edit_original_response(content=msg, embed=None, view=None)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return

        teams = data.get("teams", [])
        total = data.get("total", len(teams))

        if not teams:
            msg = build_no_results_msg("équipe LFP", role, min_rank, max_rank)
            if edit:
                await interaction.edit_original_response(content=msg, embed=None, view=None)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return

        title = "Équipes LFP"
        if role:
            emoji = ROLE_EMOJIS.get(role, "")
            name = ROLE_NAMES.get(role, role)
            title += f" — {emoji} {name}"

        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        embed = discord.Embed(title=title, color=0xE67E22)

        for t in teams:
            team_name = t["name"]
            wanted = t.get("wanted_roles") or []
            wanted_str = ", ".join(
                f"{ROLE_EMOJIS.get(r, '')} {ROLE_NAMES.get(r, r)}" for r in wanted
            ) if wanted else "Tous rôles"
            rank_range = ""
            if t.get("min_rank") or t.get("max_rank"):
                rp = []
                if t.get("min_rank"):
                    rp.append(t["min_rank"].capitalize())
                if t.get("max_rank"):
                    rp.append(t["max_rank"].capitalize())
                rank_range = " → ".join(rp)
            member_count = len(t.get("members", []))
            link = f"{APP_URL}/t/{t['slug']}"

            lines = [f"Cherche : {wanted_str}"]
            if rank_range:
                lines.append(f"Elo : {rank_range}")
            lines.append(f"Roster : {member_count}/5")

            info_parts = build_info_parts(t)
            if info_parts:
                lines.append(" · ".join(info_parts))

            lines.append(f"[Voir l'équipe]({link})")

            embed.add_field(name=team_name, value="\n".join(lines), inline=False)

        embed.set_footer(text=f"Page {page + 1}/{total_pages} · {total} équipes LFP au total")

        filters_encoded = encode_list_filters(role, min_rank, max_rank)
        view = build_nav_view("rt_lft_page", page, total, PAGE_SIZE, filters_encoded)

        for t in teams:
            captain_id = t.get("captain_discord_id")
            if captain_id:
                label = f"Contacter {t['name']}"
                if len(label) > 80:
                    label = label[:77] + "..."
                view.add_item(discord.ui.Button(
                    label=label,
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"rt_contact:{captain_id}",
                ))

        view.add_item(discord.ui.Button(
            label="Parcourir les équipes",
            style=discord.ButtonStyle.link,
            url=f"{APP_URL}/browse?tab=teams",
        ))

        if edit:
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="rt-lft", description="Équipes qui cherchent des joueurs")
    @app_commands.describe(
        role="Filtrer par rôle recherché",
        min_rank="Rang minimum",
        max_rank="Rang maximum",
    )
    @app_commands.choices(role=ROLE_CHOICES, min_rank=RANK_CHOICES, max_rank=RANK_CHOICES)
    async def rt_lft(
        self,
        interaction: discord.Interaction,
        role: app_commands.Choice[str] | None = None,
        min_rank: app_commands.Choice[str] | None = None,
        max_rank: app_commands.Choice[str] | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        await self._fetch_lft_and_respond(
            interaction,
            page=0,
            role=role.value if role else None,
            min_rank=min_rank.value if min_rank else None,
            max_rank=max_rank.value if max_rank else None,
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")  # type: ignore[union-attr]
        if not custom_id.startswith("rt_lft_page:"):
            return

        parts = custom_id[len("rt_lft_page:"):].split(":", 1)
        try:
            page = int(parts[0])
        except (ValueError, IndexError):
            return
        role, min_rank, max_rank = decode_list_filters(parts[1]) if len(parts) > 1 else (None, None, None)

        await interaction.response.defer(ephemeral=True)
        await self._fetch_lft_and_respond(interaction, page, role, min_rank, max_rank, edit=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TeamCog(bot))
