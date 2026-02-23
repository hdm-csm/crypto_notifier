from app.bots.discord.custom.custom_context import CustomContext
from app.services.account_lookup_service import AccountLookupService
from discord.ext import commands
from app.bots.discord.custom.custom_tree import CustomTree
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.vs_currency_service import VsCurrencyService


class CustomDiscordBot(commands.Bot):
    """Custom bot that uses CustomContext for all commands."""

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        crypto_currency_service: CryptoCurrencyService,
        vs_currency_service: VsCurrencyService,
        **kwargs,
    ):

        super().__init__(tree_cls=lambda bot: CustomTree(bot, account_lookup_service), **kwargs)  # type: ignore[arg-type]
        self.account_lookup_service = account_lookup_service
        self.crypto_currency_service = crypto_currency_service
        self.vs_currency_service = vs_currency_service

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)
