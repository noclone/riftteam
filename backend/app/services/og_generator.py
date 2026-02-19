import asyncio
import os
from io import BytesIO
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageFont

from shared.constants import ACTIVITY_LABELS, AMBIANCE_LABELS, RANK_COLORS
from shared.format import format_rank, format_win_rate

ROLE_LABELS_SHORT: dict[str, str] = {
    "TOP": "Top",
    "JUNGLE": "Jungle",
    "MIDDLE": "Mid",
    "BOTTOM": "ADC",
    "UTILITY": "Support",
}

CARD_W, CARD_H = 1200, 630
ICON_DIR = Path(os.environ.get("ICON_CACHE_DIR", "/tmp/riftteam_icons"))
DDRAGON_VERSION: str | None = None


def _hex_to_rgb(hex_int: int) -> tuple[int, int, int]:
    """Convert a 0xRRGGBB integer to an (R, G, B) tuple."""
    return ((hex_int >> 16) & 0xFF, (hex_int >> 8) & 0xFF, hex_int & 0xFF)


def _rank_rgb(tier: str | None) -> tuple[int, int, int]:
    """Return the RGB color associated with a rank tier."""
    if not tier:
        return (100, 100, 100)
    return _hex_to_rgb(RANK_COLORS.get(tier.upper(), 0x6B6B6B))


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a DejaVu font from common system paths, falling back to the default."""
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
    """Fetch and cache the latest Data Dragon version string."""
    global DDRAGON_VERSION
    if DDRAGON_VERSION:
        return DDRAGON_VERSION
    async with aiohttp.ClientSession() as session, session.get("https://ddragon.leagueoflegends.com/api/versions.json") as resp:
        versions = await resp.json()
    DDRAGON_VERSION = versions[0]
    return DDRAGON_VERSION


async def _download_icon(url: str, filename: str) -> Image.Image | None:
    """Download an image and cache it on disk, returning None on failure."""
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = ICON_DIR / filename
    if cache_path.exists():
        try:
            return Image.open(cache_path).convert("RGBA")
        except Exception:
            cache_path.unlink(missing_ok=True)
    try:
        async with aiohttp.ClientSession() as session, session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
        cache_path.write_bytes(data)
        return Image.open(BytesIO(data)).convert("RGBA")
    except Exception:
        return None


async def _get_rank_icon(tier: str) -> Image.Image | None:
    """Fetch the rank crest icon from CommunityDragon."""
    tier_lower = tier.lower()
    url = f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests/{tier_lower}.png"
    return await _download_icon(url, f"rank_{tier_lower}.png")


async def _get_role_icon(role: str) -> Image.Image | None:
    """Fetch a role/position icon from CommunityDragon."""
    role_lower = role.lower()
    url = f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-clash/global/default/assets/images/position-selector/positions/icon-position-{role_lower}.png"
    return await _download_icon(url, f"role_{role_lower}.png")


async def _get_champion_icon(champion_name: str) -> Image.Image | None:
    """Fetch a champion square icon from Data Dragon."""
    version = await _get_ddragon_version()
    safe_name = champion_name.replace(" ", "").replace("'", "")
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{safe_name}.png"
    return await _download_icon(url, f"champ_{safe_name}.png")


def _paste_rounded(dst: Image.Image, src: Image.Image, pos: tuple[int, int], size: int, radius: int) -> None:
    """Paste an image with rounded-rectangle clipping onto a destination."""
    src = src.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    dst.paste(src, pos, mask)


def _paste_icon(dst: Image.Image, src: Image.Image, pos: tuple[int, int], size: int) -> None:
    """Resize and paste an icon, preserving alpha transparency."""
    src = src.resize((size, size), Image.LANCZOS)
    if src.mode == "RGBA":
        dst.paste(src, pos, src)
    else:
        dst.paste(src, pos)




def _draw_chips(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    chips: list[tuple[str, tuple[int, int, int], tuple[int, int, int]]],
    y: int,
    cx: int,
) -> None:
    """Draw a row of colored pill chips centered at (cx, y)."""
    font = _load_font(32, bold=True)
    pad_x, gap = 24, 16
    radius = 22

    widths = []
    for label, _, _ in chips:
        bbox = draw.textbbox((0, 0), label, font=font)
        widths.append(bbox[2] - bbox[0] + pad_x * 2)

    total_w = sum(widths) + gap * (len(chips) - 1)
    x = cx - total_w // 2

    for i, (label, text_color, bg_color) in enumerate(chips):
        w = widths[i]
        h = 44
        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=bg_color)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        tx = x + (w - tw) // 2
        ty = y + (h - (bbox[3] - bbox[1])) // 2 - bbox[1]
        draw.text((tx, ty), label, fill=text_color, font=font)
        x += w + gap


async def generate_og_image(player: dict, champions: list[dict]) -> bytes:
    """Render a 1200x630 PNG Open Graph card for a player profile."""
    rank_color = _rank_rgb(player.get("rank_solo_tier"))
    dark = (24, 24, 32)

    img = Image.new("RGB", (CARD_W, CARD_H), dark)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, CARD_W, 8], fill=rank_color)

    font_name = _load_font(56, bold=True)
    font_role = _load_font(40, bold=True)
    font_rank = _load_font(52, bold=True)
    font_lp = _load_font(40)
    font_brand = _load_font(24)

    cx = CARD_W // 2

    riot_id = f"{player.get('riot_game_name', '')}#{player.get('riot_tag_line', '')}"
    primary = player.get("primary_role")
    secondary = player.get("secondary_role")
    roles: list[str] = []
    if primary:
        roles.append(primary)
    if secondary:
        roles.append(secondary)
    role_icons = await asyncio.gather(*[_get_role_icon(r) for r in roles]) if roles else []

    icon_size = 38
    icon_gap = 4
    role_gap = 10

    id_bbox = draw.textbbox((0, 0), riot_id, font=font_name)
    id_w = id_bbox[2] - id_bbox[0]

    role_parts_w = 0
    for i, role in enumerate(roles):
        label = ROLE_LABELS_SHORT.get(role, role)
        lbbox = draw.textbbox((0, 0), label, font=font_role)
        part_w = icon_size + icon_gap + (lbbox[2] - lbbox[0])
        role_parts_w += part_w
        if i > 0:
            role_parts_w += role_gap

    gap = 16 if roles else 0
    total_w = id_w + gap + role_parts_w
    header_x = cx - total_w // 2
    header_y = 30

    name_cap = draw.textbbox((0, header_y), "A", font=font_name)
    name_mid = (name_cap[1] + name_cap[3]) // 2

    draw.text((header_x, header_y), riot_id, fill=(255, 255, 255), font=font_name)
    role_x = header_x + id_w + gap
    role_cap = draw.textbbox((0, 0), "A", font=font_role)
    role_text_y = name_mid - (role_cap[3] - role_cap[1]) // 2 - role_cap[1]
    for i, role in enumerate(roles):
        if i > 0:
            role_x += role_gap
        icon = role_icons[i]
        if icon:
            icon_y = name_mid - icon_size // 2
            _paste_icon(img, icon, (role_x, icon_y), icon_size)
        role_x += icon_size + icon_gap
        label = ROLE_LABELS_SHORT.get(role, role)
        color = (100, 180, 255) if i == 0 else (80, 130, 190)
        draw.text((role_x, role_text_y), label, fill=color, font=font_role)
        lbbox = draw.textbbox((0, 0), label, font=font_role)
        role_x += lbbox[2] - lbbox[0]

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

        for i, _champ in enumerate(top_champs):
            col = i % 3
            row = i // 3
            x = grid_x + col * (icon_size + gap)
            y = grid_y + row * (icon_size + gap)
            icon = champ_icons[i]
            if icon:
                _paste_rounded(img, icon, (x, y), icon_size, 14)
            else:
                draw.rounded_rectangle([x, y, x + icon_size, y + icon_size], radius=14, fill=(40, 40, 55))

    row1: list[tuple[str, tuple[int, int, int], tuple[int, int, int]]] = []
    row2: list[tuple[str, tuple[int, int, int], tuple[int, int, int]]] = []
    activities = player.get("activities") or []
    for a in activities:
        row1.append((ACTIVITY_LABELS.get(a, a), (103, 232, 249), (21, 48, 61)))
    ambiance = player.get("ambiance")
    if ambiance:
        if ambiance == "TRYHARD":
            row2.append((AMBIANCE_LABELS.get(ambiance, ambiance), (216, 180, 254), (49, 29, 72)))
        else:
            row2.append((AMBIANCE_LABELS.get(ambiance, ambiance), (134, 239, 172), (24, 52, 40)))
    freq_min = player.get("frequency_min")
    freq_max = player.get("frequency_max")
    if freq_min is not None and freq_max is not None:
        freq = f"{freq_min}x/sem" if freq_min == freq_max else f"{freq_min}-{freq_max}x/sem"
        row2.append((freq, (209, 213, 219), (40, 45, 57)))
    if row1:
        _draw_chips(img, draw, row1, CARD_H - 120 - (56 if row2 else 0), cx)
    if row2:
        _draw_chips(img, draw, row2, CARD_H - 120, cx)

    draw.text((CARD_W - 200, CARD_H - 48), "riftteam.fr", fill=(70, 70, 90), font=font_brand)

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


async def generate_team_og_image(team: dict) -> bytes:
    """Render a 1200x630 PNG Open Graph card for a team profile."""
    dark = (24, 24, 32)
    min_tier = team.get("min_rank")
    rank_color = _rank_rgb(min_tier)

    img = Image.new("RGB", (CARD_W, CARD_H), dark)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, CARD_W, 8], fill=rank_color)

    font_name = _load_font(56, bold=True)
    font_sub = _load_font(34, bold=True)
    font_role = _load_font(28, bold=True)
    font_lp = _load_font(22)
    font_brand = _load_font(24)

    cx = CARD_W // 2

    name = team.get("name", "")
    name_bbox = draw.textbbox((0, 0), name, font=font_name)
    name_w = name_bbox[2] - name_bbox[0]
    draw.text((cx - name_w // 2, 30), name, fill=(255, 255, 255), font=font_name)

    min_r = team.get("min_rank")
    max_r = team.get("max_rank")
    if min_r or max_r:
        rank_icon_size = 40
        arrow_text = " → "
        parts_w = 0
        if min_r:
            min_label = min_r.capitalize()
            min_bbox = draw.textbbox((0, 0), min_label, font=font_sub)
            parts_w += rank_icon_size + 6 + (min_bbox[2] - min_bbox[0])
        if min_r and max_r:
            arrow_bbox = draw.textbbox((0, 0), arrow_text, font=font_sub)
            parts_w += arrow_bbox[2] - arrow_bbox[0]
        if max_r:
            max_label = max_r.capitalize()
            max_bbox = draw.textbbox((0, 0), max_label, font=font_sub)
            parts_w += rank_icon_size + 6 + (max_bbox[2] - max_bbox[0])

        rank_icons = await asyncio.gather(
            _get_rank_icon(min_r) if min_r else asyncio.sleep(0),
            _get_rank_icon(max_r) if max_r else asyncio.sleep(0),
        )
        min_rank_icon = rank_icons[0] if min_r else None
        max_rank_icon = rank_icons[1] if max_r else None

        rx = cx - parts_w // 2
        ry = 100
        cap_bbox = draw.textbbox((0, ry), "A", font=font_sub)
        text_mid = (cap_bbox[1] + cap_bbox[3]) // 2

        if min_r:
            if min_rank_icon:
                _paste_icon(img, min_rank_icon, (rx, text_mid - rank_icon_size // 2), rank_icon_size)
            rx += rank_icon_size + 6
            draw.text((rx, ry), min_r.capitalize(), fill=_rank_rgb(min_r), font=font_sub)
            t_bbox = draw.textbbox((0, 0), min_r.capitalize(), font=font_sub)
            rx += t_bbox[2] - t_bbox[0]
        if min_r and max_r:
            draw.text((rx, ry), arrow_text, fill=(150, 150, 170), font=font_sub)
            a_bbox = draw.textbbox((0, 0), arrow_text, font=font_sub)
            rx += a_bbox[2] - a_bbox[0]
        if max_r:
            if max_rank_icon:
                _paste_icon(img, max_rank_icon, (rx, text_mid - rank_icon_size // 2), rank_icon_size)
            rx += rank_icon_size + 6
            draw.text((rx, ry), max_r.capitalize(), fill=_rank_rgb(max_r), font=font_sub)

    members = team.get("members", [])
    wanted_roles = team.get("wanted_roles", [])
    slot_y = 170
    slot_x = 80
    slot_gap = (CARD_W - 160) // 5

    all_roles = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    member_by_role: dict[str, dict] = {}
    for m in members:
        player = m.get("player", m)
        member_by_role[m.get("role", "")] = player

    role_rank_icons = await asyncio.gather(
        *[_get_rank_icon(member_by_role[r]["rank_solo_tier"]) if r in member_by_role and member_by_role[r].get("rank_solo_tier") else asyncio.sleep(0) for r in all_roles]
    )
    role_position_icons = await asyncio.gather(*[_get_role_icon(r) for r in all_roles])

    for i, role in enumerate(all_roles):
        x = slot_x + i * slot_gap
        player = member_by_role.get(role)
        is_wanted = role in wanted_roles
        slot_cx = x + slot_gap // 2

        pos_icon = role_position_icons[i]
        role_label = ROLE_LABELS_SHORT.get(role, role)
        role_bbox_t = draw.textbbox((0, 0), role_label, font=font_role)
        role_tw = role_bbox_t[2] - role_bbox_t[0]
        pos_icon_size = 28
        pos_gap = 4
        role_total_w = (pos_icon_size + pos_gap if pos_icon else 0) + role_tw
        role_start_x = slot_cx - role_total_w // 2

        if pos_icon:
            cap_bbox = draw.textbbox((0, slot_y), "A", font=font_role)
            pos_mid = (cap_bbox[1] + cap_bbox[3]) // 2
            _paste_icon(img, pos_icon, (role_start_x, pos_mid - pos_icon_size // 2), pos_icon_size)
            role_start_x += pos_icon_size + pos_gap
        draw.text((role_start_x, slot_y), role_label, fill=(100, 180, 255), font=font_role)

        box_y = slot_y + 45
        box_w = slot_gap - 20
        box_h = 120
        bx = x + 10

        if player:
            draw.rounded_rectangle([bx, box_y, bx + box_w, box_y + box_h], radius=10, fill=(40, 40, 55))
            tier = player.get("rank_solo_tier")
            rank_img = role_rank_icons[i]
            r_icon_size = 70
            if rank_img:
                icon_x = bx + (box_w - r_icon_size) // 2
                _paste_icon(img, rank_img, (icon_x, box_y + 8), r_icon_size)
            lp = player.get("rank_solo_lp")
            if lp is not None and tier:
                lp_text = f"{lp} LP"
                lp_bbox = draw.textbbox((0, 0), lp_text, font=font_lp)
                lp_w = lp_bbox[2] - lp_bbox[0]
                draw.text((bx + (box_w - lp_w) // 2, box_y + 82), lp_text, fill=_rank_rgb(tier), font=font_lp)
            elif not tier:
                u_text = "Unranked"
                u_bbox = draw.textbbox((0, 0), u_text, font=font_lp)
                u_w = u_bbox[2] - u_bbox[0]
                draw.text((bx + (box_w - u_w) // 2, box_y + box_h // 2 - 10), u_text, fill=(100, 100, 100), font=font_lp)
        elif is_wanted:
            draw.rounded_rectangle([bx, box_y, bx + box_w, box_y + box_h], radius=10, outline=(100, 180, 255), width=2)
            q_bbox = draw.textbbox((0, 0), "?", font=font_name)
            q_w = q_bbox[2] - q_bbox[0]
            draw.text((bx + box_w // 2 - q_w // 2, box_y + 25), "?", fill=(100, 180, 255), font=font_name)
        else:
            draw.rounded_rectangle([bx, box_y, bx + box_w, box_y + box_h], radius=10, fill=(30, 30, 40))

    row1: list[tuple[str, tuple[int, int, int], tuple[int, int, int]]] = []
    row2: list[tuple[str, tuple[int, int, int], tuple[int, int, int]]] = []
    activities = team.get("activities") or []
    for a in activities:
        row1.append((ACTIVITY_LABELS.get(a, a), (103, 232, 249), (21, 48, 61)))
    ambiance = team.get("ambiance")
    if ambiance:
        if ambiance == "TRYHARD":
            row2.append((AMBIANCE_LABELS.get(ambiance, ambiance), (216, 180, 254), (49, 29, 72)))
        else:
            row2.append((AMBIANCE_LABELS.get(ambiance, ambiance), (134, 239, 172), (24, 52, 40)))
    freq_min = team.get("frequency_min")
    freq_max = team.get("frequency_max")
    if freq_min is not None and freq_max is not None:
        freq = f"{freq_min}x/sem" if freq_min == freq_max else f"{freq_min}-{freq_max}x/sem"
        row2.append((freq, (209, 213, 219), (40, 45, 57)))
    if row1:
        _draw_chips(img, draw, row1, CARD_H - 120 - (56 if row2 else 0), cx)
    if row2:
        _draw_chips(img, draw, row2, CARD_H - 120, cx)

    draw.text((CARD_W - 200, CARD_H - 48), "riftteam.fr", fill=(70, 70, 90), font=font_brand)

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
