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
    """Format a rank as a human-readable string (e.g. 'Emerald II (45 LP)')."""
    if not tier:
        return "Unranked"
    label = tier.capitalize()
    if division and tier.upper() not in APEX_TIERS:
        label += f" {division}"
    if lp is not None:
        label += f" ({lp} LP)"
    return label


def format_win_rate(wins: int | None, losses: int | None, *, include_games: bool = False) -> str:
    """Format win rate as a percentage string, optionally with total games."""
    w = wins or 0
    lo = losses or 0
    total = w + lo
    if total == 0:
        return ""
    pct = round(w / total * 100)
    if include_games:
        return f"{pct}% WR ({total}G)"
    return f"{pct}% WR"


def format_rank_range(
    min_rank: str | None, max_rank: str | None, *, abbreviated: bool = False
) -> str:
    """Format a rank range (e.g. 'Gold → Diamond') or 'Tous elos' if unbounded."""
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
