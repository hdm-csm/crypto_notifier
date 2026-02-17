import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes
from app.bots.telegram.modules.crypto_info_module import CryptoInfoModule
from app.bots.telegram.modules.favorites_module import FavoritesModule
from app.bots.telegram.modules.notifications_module import NotificationsModule
from app.bots.telegram.modules.base import AccountModule
from app.bots.telegram.modules.settings_module import SettingsModule
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.services.favorites_service import FavoritesService
from app.services.notification_service import NotificationService
from app.services.vs_currency_service import VsCurrencyService
from app.utils.exceptions import MissingCommandArguments
from app.utils.functions import get_command_example


class TelegramBot:

    PLATFORM_TYPE = PlatformType.TELEGRAM

    def __init__(
        self,
        token: str,
        account_lookup_service: AccountLookupService,
        crypto_api_service: CryptoApiService,
        favorites_service: FavoritesService,
        notification_service: NotificationService,
        vs_currency_service: VsCurrencyService,
    ):
        self._token = token

        self._app = ApplicationBuilder().token(token).build()
        self._app.add_error_handler(self._error_handler)

        self._modules: list[AccountModule] = [
            FavoritesModule(self._app, account_lookup_service, favorites_service),
            NotificationsModule(self._app, account_lookup_service, notification_service),
            CryptoInfoModule(self._app, account_lookup_service, crypto_api_service),
            SettingsModule(self._app, account_lookup_service, vs_currency_service),
        ]

        for module in self._modules:
            module.register()

    async def start(self):
        """Start the Telegram bot."""
        await self._app.initialize()

        # Register job queue handlers after initialization
        for module in self._modules:
            if module.register_jobs is not None:
                module.register_jobs()

        await self._app.start()
        if self._app.updater is not None:
            await self._app.updater.start_polling(
                poll_interval=0.0,
                timeout=60,
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,
            )
        logging.info("TelegramBot has started!")

    async def stop(self):
        """Stop the Telegram bot."""
        if self._app.updater is not None:
            await self._app.updater.stop()
        await self._app.stop()
        await self._app.shutdown()

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Global error handler for all Telegram commands."""
        logging.error(f"Telegram error: {type(context.error).__name__} - {context.error}")

        # Only respond to user if we have an update with a message
        if isinstance(update, Update) and update.message:
            error_message = f"❌ An error occurred: {str(context.error)}"

            # Handle MissingCommandArguments with usage examples
            if isinstance(context.error, MissingCommandArguments):
                command_name = context.error.command_name
                error_message += get_command_example(command_name)
            else:
                # Try to extract command name from the message for other errors
                if update.message.text and update.message.text.startswith("/"):
                    command_parts = update.message.text.split()
                    command_name = command_parts[0][1:]  # Remove the leading /
                    error_message += get_command_example(command_name)

            await update.message.reply_text(error_message)
