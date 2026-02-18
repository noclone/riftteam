import asyncio
from io import BytesIO
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageFont

from shared.constants import RANK_COLORS
from shared.format import format_rank, format_win_rate

ROLE_LABELS_FULL: dict[str, str] = {
    "TOP": "Toplaner",
    "JUNGLE": "Jungler",
    "MIDDLE": "Midlaner",
    "BOTTOM": "ADC",
    "UTILITY": "Support",
}

CARD_W, CARD_H = 1200, 630
ICON_DIR = Path("/tmp/riftteam_icons")
DDRAGON_VERSION: str | None = None


def _hex_to_rgb(hex_int: int) -> tuple[int, int, int]:
    return ((hex_int >> 16) & 0xFF, (hex_int >> 8) & 0xFF, hex_int & 0xFF)


def _rank_rgb(tier: str | None) -> tuple[int, int, int]:
    if not tier:
        return (100, 100, 100)
    return _hex_to_rgb(RANK_COLORS.get(tier.upper(), 0x6B6B6B))


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = (
        ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]
        if bold
        else ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf"]
    )
    for name in names:
        for d in ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/TTF", "/usr/share/fonts"]:
            p = Path(d) / name
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size)


async def _get_ddragon_version() -> str:
    global DDRAGON_VERSION
    if DDRAGON_VERSION:
        return DDRAGON_VERSION
    async with aiohttp.ClientSession() as session:
        async with session.get("https://ddragon.leagueoflegends.com/api/versions.json") as resp:
            versions = await resp.json()
    DDRAGON_VERSION = versions[0]
    return DDRAGON_VERSION


async def _download_icon(url: str, filename: str) -> Image.Image | None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = ICON_DIR / filename
    if cache_path.exists():
        try:
            return Image.open(cache_path).convert("RGBA")
        except Exception:
            cache_path.unlink(missing_ok=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
        cache_path.write_bytes(data)
        return Image.open(BytesIO(data)).convert("RGBA")
    except Exception:
        return None


async def _get_rank_icon(tier: str) -> Image.Image | None:
    tier_lower = tier.lower()
    url = f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests/{tier_lower}.png"
    return await _download_icon(url, f"rank_{tier_lower}.png")


async def _get_champion_icon(champion_name: str) -> Image.Image | None:
    version = await _get_ddragon_version()
    safe_name = champion_name.replace(" ", "").replace("'", "")
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{safe_name}.png"
    return await _download_icon(url, f"champ_{safe_name}.png")


def _paste_rounded(dst: Image.Image, src: Image.Image, pos: tuple[int, int], size: int, radius: int) -> None:
    src = src.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    dst.paste(src, pos, mask)


def _paste_icon(dst: Image.Image, src: Image.Image, pos: tuple[int, int], size: int) -> None:
    src = src.resize((size, size), Image.LANCZOS)
    if src.mode == "RGBA":
        dst.paste(src, pos, src)
    else:
        dst.paste(src, pos)




async def generate_og_image(player: dict, champions: list[dict]) -> bytes:
    rank_color = _rank_rgb(player.get("rank_solo_tier"))
    dark = (24, 24, 32)

    img = Image.new("RGB", (CARD_W, CARD_H), dark)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, CARD_W, 8], fill=rank_color)

    font_name = _load_font(56, bold=True)
    font_wr = _load_font(34)
    font_rank = _load_font(52, bold=True)
    font_lp = _load_font(40)
    font_brand = _load_font(24)

    cx = CARD_W // 2

    riot_id = f"{player.get('riot_game_name', '')}#{player.get('riot_tag_line', '')}"
    primary = player.get("primary_role")
    role_label = ROLE_LABELS_FULL.get(primary, "") if primary else ""

    id_bbox = draw.textbbox((0, 0), riot_id, font=font_name)
    id_w = id_bbox[2] - id_bbox[0]
    role_bbox = draw.textbbox((0, 0), role_label, font=font_name) if role_label else (0, 0, 0, 0)
    role_w = role_bbox[2] - role_bbox[0] if role_label else 0
    gap = 30 if role_label else 0
    total_w = id_w + gap + role_w
    header_x = cx - total_w // 2

    draw.text((header_x, 30), riot_id, fill=(255, 255, 255), font=font_name)
    if role_label:
        draw.text((header_x + id_w + gap, 30), role_label, fill=(100, 180, 255), font=font_name)

    rank_tier = player.get("rank_solo_tier")
    rank_icon_size = 200
    left_x = 60
    rank_y = 140

    if rank_tier:
        rank_img = await _get_rank_icon(rank_tier)
        if rank_img:
            _paste_icon(img, rank_img, (left_x, rank_y), rank_icon_size)

    text_x = left_x + rank_icon_size + 20
    rank_text = format_rank(rank_tier, player.get("rank_solo_division"))
    draw.text((text_x, rank_y + 20), rank_text, fill=rank_color, font=font_rank)

    lp = player.get("rank_solo_lp")
    if lp is not None and rank_tier:
        draw.text((text_x, rank_y + 85), f"{lp} LP", fill=(180, 180, 200), font=font_lp)

    wr = format_win_rate(player.get("rank_solo_wins"), player.get("rank_solo_losses"))
    if wr:
        draw.text((text_x, rank_y + 140), wr, fill=(160, 160, 180), font=font_lp)

    top_champs = sorted(champions, key=lambda c: c.get("games_played", 0), reverse=True)[:6]
    if top_champs:
        champ_icons = await asyncio.gather(
            *[_get_champion_icon(c.get("champion_name", "")) for c in top_champs]
        )

        icon_size = 110
        gap = 16
        grid_w = 3 * icon_size + 2 * gap
        grid_x = CARD_W - 60 - grid_w
        grid_y = rank_y + 10

        for i, champ in enumerate(top_champs):
            col = i % 3
            row = i // 3
            x = grid_x + col * (icon_size + gap)
            y = grid_y + row * (icon_size + gap)
            icon = champ_icons[i]
            if icon:
                _paste_rounded(img, icon, (x, y), icon_size, 14)
            else:
                draw.rounded_rectangle([x, y, x + icon_size, y + icon_size], radius=14, fill=(40, 40, 55))

    ACTIVITY_LABELS = {
        "SCRIMS": "Scrims",
        "TOURNOIS": "Tournois",
        "LAN": "LAN",
        "FLEX": "Flex",
        "CLASH": "Clash",
    }
    activities = player.get("activities") or []
    if activities:
        font_activities = _load_font(48, bold=True)
        label = ", ".join(ACTIVITY_LABELS.get(a, a) for a in activities)
        bbox = draw.textbbox((0, 0), label, font=font_activities)
        draw.text((cx - (bbox[2] - bbox[0]) // 2, CARD_H - 105), label, fill=(255, 255, 255), font=font_activities)

    draw.text((CARD_W - 200, CARD_H - 48), "riftteam.gg", fill=(70, 70, 90), font=font_brand)

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


async def generate_team_og_image(team: dict) -> bytes:
    dark = (24, 24, 32)
    min_tier = team.get("min_rank")
    rank_color = _rank_rgb(min_tier)

    img = Image.new("RGB", (CARD_W, CARD_H), dark)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, CARD_W, 8], fill=rank_color)

    font_name = _load_font(56, bold=True)
    font_sub = _load_font(34)
    font_role = _load_font(28, bold=True)
    font_member = _load_font(26)
    font_brand = _load_font(24)

    cx = CARD_W // 2

    name = team.get("name", "")
    name_bbox = draw.textbbox((0, 0), name, font=font_name)
    name_w = name_bbox[2] - name_bbox[0]
    draw.text((cx - name_w // 2, 30), name, fill=(255, 255, 255), font=font_name)

    min_r = team.get("min_rank")
    max_r = team.get("max_rank")
    if min_r or max_r:
        rank_text = ""
        if min_r:
            rank_text = min_r.capitalize()
        if max_r:
            rank_text += f" → {max_r.capitalize()}"
        rank_bbox = draw.textbbox((0, 0), rank_text, font=font_sub)
        rank_w = rank_bbox[2] - rank_bbox[0]
        draw.text((cx - rank_w // 2, 100), rank_text, fill=rank_color, font=font_sub)

    roles = team.get("wanted_roles", [])
    members = team.get("members", [])
    slot_y = 170
    slot_x = 80
    slot_gap = (CARD_W - 160) // 5

    all_roles = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    member_by_role = {}
    for m in members:
        member_by_role[m.get("role", "")] = m

    for i, role in enumerate(all_roles):
        x = slot_x + i * slot_gap
        member = member_by_role.get(role)
        is_wanted = role in roles

        role_label = ROLE_LABELS_FULL.get(role, role)
        role_bbox = draw.textbbox((0, 0), role_label, font=font_role)
        role_w = role_bbox[2] - role_bbox[0]
        draw.text((x + slot_gap // 2 - role_w // 2, slot_y), role_label, fill=(100, 180, 255), font=font_role)

        box_y = slot_y + 40
        box_w = slot_gap - 20
        box_h = 120
        bx = x + 10

        if member:
            draw.rounded_rectangle([bx, box_y, bx + box_w, box_y + box_h], radius=10, fill=(40, 40, 55))
            riot_id = f"{member.get('riot_game_name', '')}#{member.get('riot_tag_line', '')}"
            tier = member.get("rank_solo_tier")
            tier_label = tier.capitalize() if tier else "Unranked"

            draw.text((bx + 10, box_y + 15), riot_id[:12], fill=(255, 255, 255), font=font_member)
            tier_color = _rank_rgb(tier)
            draw.text((bx + 10, box_y + 50), tier_label, fill=tier_color, font=font_member)
        elif is_wanted:
            draw.rounded_rectangle([bx, box_y, bx + box_w, box_y + box_h], radius=10, outline=(100, 180, 255), width=2)
            q_bbox = draw.textbbox((0, 0), "?", font=font_name)
            q_w = q_bbox[2] - q_bbox[0]
            draw.text((bx + box_w // 2 - q_w // 2, box_y + 25), "?", fill=(100, 180, 255), font=font_name)
        else:
            draw.rounded_rectangle([bx, box_y, bx + box_w, box_y + box_h], radius=10, fill=(30, 30, 40))

    ACTIVITY_LABELS = {
        "SCRIMS": "Scrims",
        "TOURNOIS": "Tournois",
        "LAN": "LAN",
        "FLEX": "Flex",
        "CLASH": "Clash",
    }
    activities = team.get("activities") or []
    if activities:
        font_activities = _load_font(48, bold=True)
        label = ", ".join(ACTIVITY_LABELS.get(a, a) for a in activities)
        bbox = draw.textbbox((0, 0), label, font=font_activities)
        draw.text((cx - (bbox[2] - bbox[0]) // 2, CARD_H - 105), label, fill=(255, 255, 255), font=font_activities)

    draw.text((CARD_W - 200, CARD_H - 48), "riftteam.gg", fill=(70, 70, 90), font=font_brand)

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
