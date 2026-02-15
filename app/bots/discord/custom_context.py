from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from discord.ext import commands
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models.schemas import Account


class CustomContext(commands.Context):
    """An extended context to use in commands with often-used data to avoid boilerplate code."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # Initialize attributes so mypy knows they exist
        self.account: Optional["Account"] = None
        self.db_session: Optional[Session] = No
