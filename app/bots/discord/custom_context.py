from __future__ import annotations

from typing import TYPE_CHECKING
from discord.ext import commands
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models.schemas import Account


class CustomContext(commands.Context):
    """An extended context to use in commands with often-used data to avoid boilerplate code."""

    account: Account
    db_session: Session
