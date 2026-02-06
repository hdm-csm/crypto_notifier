from __future__ import annotations

from discord.ext import commands
from app.models.schemas import Account


class CustomContext(commands.Context):
    """An extended context to use in commands with account attribute."""

    account: Account
