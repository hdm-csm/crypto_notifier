import logging
from telegram.ext import ApplicationBuilder
from app.bots.telegram.modules.crypto_info_module import CryptoInfoModule
from app.bots.telegram.modules.favorites_module import FavoritesModule
from app.bots.telegram.modules.base import TelegramModule
from app.bots.telegram.modules.settings_module import SettingsModule
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.services.favorites_service import FavoritesService
from app.services.vs_currency_service import VsCurrencyService


class TelegramBot:

    PLATFORM_TYPE = PlatformType.TELEGRAM

    def __init__(
        self,
        token: str,
        account_lookup_service: AccountLookupService,
        crypto_api_service: CryptoApiService,
        favorites_service: FavoritesService,
        vs_currency_service: VsCurrencyService,
    ):
        self._token = token
        self._account_lookup_service = account_lookup_service
        self._crypto_api_service = crypto_api_service
        self._favorites_service = favorites_service
        self._vs_currency_service = vs_currency_service

        self.app = ApplicationBuilder().token(token).build()

        modules: list[TelegramModule] = [
            FavoritesModule(account_lookup_service, favorites_service),
            CryptoInfoModule(account_lookup_service, crypto_api_service),
            SettingsModule(account_lookup_service, vs_currency_service),
        ]

        for module in modules:
            module.register(self.app)

    async def start(self):
        """Start the Telegram bot."""
        await self.app.initialize()
        await self.app.start()
        if self.app.updater is not None:
            await self.app.updater.start_polling(
                poll_interval=0.0,
                timeout=60,
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,
            )
        logging.info("TelegramBot has started!")

    async def stop(self):
        """Stop the Telegram bot."""
        if self.app.updater is not None:
            await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
