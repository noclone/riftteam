from shared.constants import RANK_ORDER


def apply_rank_filters(stmt, count_stmt, min_rank, max_rank, column, *, allow_null=False):
    """Add WHERE clauses filtering rows to those within a rank range."""
    if min_rank and min_rank.upper() in RANK_ORDER:
        min_val = RANK_ORDER[min_rank.upper()]
        valid_tiers = [t for t, v in RANK_ORDER.items() if v >= min_val]
        cond = column.in_(valid_tiers)
        if allow_null:
            cond = cond | column.is_(None)
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if max_rank and max_rank.upper() in RANK_ORDER:
        max_val = RANK_ORDER[max_rank.upper()]
        valid_tiers = [t for t, v in RANK_ORDER.items() if v <= max_val]
        cond = column.in_(valid_tiers)
        if allow_null:
            cond = cond | column.is_(None)
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    return stmt, count_stmt
