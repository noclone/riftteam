RANK_ORDER: dict[str, int] = {
    "IRON": 0,
    "BRONZE": 1,
    "SILVER": 2,
    "GOLD": 3,
    "PLATINUM": 4,
    "EMERALD": 5,
    "DIAMOND": 6,
    "MASTER": 7,
    "GRANDMASTER": 8,
    "CHALLENGER": 9,
}

DIVISION_ORDER: dict[str, int] = {"IV": 0, "III": 1, "II": 2, "I": 3}

ROLE_NAMES: dict[str, str] = {
    "TOP": "Top",
    "JUNGLE": "Jungle",
    "MIDDLE": "Mid",
    "BOTTOM": "ADC",
    "UTILITY": "Support",
}

ROLE_EMOJIS: dict[str, str] = {
    "TOP": "<:iconpositiontop:1473367385485611170>",
    "JUNGLE": "<:iconpositionjungle:1473367327578918922>",
    "MIDDLE": "<:iconpositionmiddle:1473367348567347449>",
    "BOTTOM": "<:iconpositionbottom:1473367295249092728>",
    "UTILITY": "<:iconpositionutility:1473367407614754846>",
}

RANK_COLORS: dict[str, int] = {
    "IRON": 0x6B6B6B,
    "BRONZE": 0x8B4513,
    "SILVER": 0xC0C0C0,
    "GOLD": 0xFFD700,
    "PLATINUM": 0x00CED1,
    "EMERALD": 0x50C878,
    "DIAMOND": 0x4169E1,
    "MASTER": 0x9B30FF,
    "GRANDMASTER": 0xDC143C,
    "CHALLENGER": 0xF0E68C,
}

ACTIVITY_CHOICES = ["SCRIMS", "TOURNOIS", "LAN", "FLEX", "CLASH"]

AMBIANCE_CHOICES = ["FUN", "TRYHARD"]

QUEUE_RANKED_SOLO = 420
QUEUE_RANKED_FLEX = 440
QUEUE_NORMAL_DRAFT = 400

SECONDARY_ROLE_THRESHOLD = 0.20
MIN_GAMES_FOR_ROLE = 10
