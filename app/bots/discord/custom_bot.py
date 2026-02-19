from app.bots.discord.custom_context import CustomContext
from app.services.account_lookup_service import AccountLookupService
from discord.ext import commands


class CustomDiscordBot(commands.Bot):
    """Custom bot that uses CustomContext for all commands."""

    def __init__(self, account_lookup_service: AccountLookupService, **kwargs):
        from app.bots.discord.custom_tree import CustomTree

        super().__init__(tree_cls=lambda bot: CustomTree(bot, account_lookup_service), **kwargs)  # type: ignore[arg-type]
        self.account_lookup_service = account_lookup_service

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)
