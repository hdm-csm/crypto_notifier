from __future__ import annotations

from discord.ext import commands
from app.models.schemas import Account
from sqlalchemy.orm import Session


class CustomContext(commands.Context):
    """An extended context to use in commands with often-used data to avoid boilerplate code."""

    account: Account
    db_session: Session
