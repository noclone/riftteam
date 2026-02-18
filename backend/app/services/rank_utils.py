from shared.constants import DIVISION_ORDER, RANK_ORDER


def rank_to_numeric(tier: str | None, division: str | None, lp: int | None) -> int:
    """Convert a rank into a single comparable integer (higher = better)."""
    if not tier:
        return -1
    tier_val = RANK_ORDER.get(tier.upper(), -1)
    div_val = DIVISION_ORDER.get(division or "", 0)
    return tier_val * 10000 + div_val * 100 + (lp or 0)


def is_higher_rank(
    tier_a: str | None, div_a: str | None, lp_a: int | None,
    tier_b: str | None, div_b: str | None, lp_b: int | None,
) -> bool:
    """Return True if rank A is strictly higher than rank B."""
    return rank_to_numeric(tier_a, div_a, lp_a) > rank_to_numeric(tier_b, div_b, lp_b)
