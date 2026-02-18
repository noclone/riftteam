APEX_TIERS = frozenset(("MASTER", "GRANDMASTER", "CHALLENGER"))

RANK_SHORT_LABELS: dict[str, str] = {
    "IRON": "Iron",
    "BRONZE": "Bronze",
    "SILVER": "Silver",
    "GOLD": "Gold",
    "PLATINUM": "Plat",
    "EMERALD": "Emerald",
    "DIAMOND": "Diam",
    "MASTER": "Master",
    "GRANDMASTER": "GM",
    "CHALLENGER": "Chall",
}


def format_rank(tier: str | None, division: str | None, lp: int | None = None) -> str:
    if not tier:
        return "Unranked"
    label = tier.capitalize()
    if division and tier.upper() not in APEX_TIERS:
        label += f" {division}"
    if lp is not None:
        label += f" ({lp} LP)"
    return label


def format_win_rate(wins: int | None, losses: int | None, *, include_games: bool = False) -> str:
    w = wins or 0
    l = losses or 0
    total = w + l
    if total == 0:
        return ""
    pct = round(w / total * 100)
    if include_games:
        return f"{pct}% WR ({total}G)"
    return f"{pct}% WR"


def format_rank_range(
    min_rank: str | None, max_rank: str | None, *, abbreviated: bool = False
) -> str:
    def _label(r: str | None) -> str:
        if not r:
            return ""
        if abbreviated:
            return RANK_SHORT_LABELS.get(r.upper(), r.capitalize())
        return r.capitalize()

    lo = _label(min_rank)
    hi = _label(max_rank)
    if lo and hi:
        return f"{lo} → {hi}" if lo != hi else lo
    return lo or hi or "Tous elos"
