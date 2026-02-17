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
    "TOP": "\U0001f6e1\ufe0f",
    "JUNGLE": "\U0001f33f",
    "MIDDLE": "\U0001f525",
    "BOTTOM": "\U0001f3f9",
    "UTILITY": "\U0001f4ab",
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

LOOKING_FOR_CHOICES = ["TEAM", "DUO", "CLASH", "SCRIM", "ANY"]

AMBITION_CHOICES = ["CHILL", "IMPROVE", "COMPETITIVE", "TRYHARD"]

QUEUE_RANKED_SOLO = 420
QUEUE_RANKED_FLEX = 440
QUEUE_NORMAL_DRAFT = 400

SECONDARY_ROLE_THRESHOLD = 0.20
MIN_GAMES_FOR_ROLE = 10
