"""Discord app_commands choices for role and rank slash-command options."""

from discord import app_commands

from shared.constants import RANK_ORDER

ROLE_CHOICES = [
    app_commands.Choice(name="Top", value="TOP"),
    app_commands.Choice(name="Jungle", value="JUNGLE"),
    app_commands.Choice(name="Mid", value="MIDDLE"),
    app_commands.Choice(name="ADC", value="BOTTOM"),
    app_commands.Choice(name="Support", value="UTILITY"),
]

RANK_CHOICES = [
    app_commands.Choice(name=k.capitalize(), value=k)
    for k in RANK_ORDER
]
