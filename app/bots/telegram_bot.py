import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ApplicationBuilder
from app.services.crypto_api_service import CryptoApiService
from app.models.schemas import PlatformType
from app.services.favorites_service import FavoritesService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)


class TelegramBot:

    PLATFORM_TYPE = PlatformType.TELEGRAM

    def __init__(
        self, token: str, crypto_api_service: CryptoApiService, favorites_service: FavoritesService
    ):
        self._token = token
        self._crypto_api_service = crypto_api_service
        self._favorites_service = favorites_service

        self.app = ApplicationBuilder().token(token).build()
        self.app.add_handler(CommandHandler("index", self.index_command, block=False))
        self.app.add_handler(CommandHandler("list", self.list_command, block=False))
        self.app.add_handler(CommandHandler("add_fav", self.add_fav_command, block=False))
        self.app.add_handler(CommandHandler("remove_fav", self.remove_fav_command, block=False))
        self.app.add_handler(CommandHandler("list_favs", self.list_favs_command, block=False))
        self.app.add_handler(CommandHandler("drop_favs", self.drop_favs_command, block=False))

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

    async def index_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None:
            return
        if not context.args:
            await update.message.reply_text(
                "Please provide a cryptocurrency name. Usage: /index bitcoin"
            )
            return
        input = context.args[0]
        result = await self._crypto_api_service.get_index(input)
        if result is None:
            await update.message.reply_text(
                f'Could not find price for "{input}".\nPlease enter correct id.'
            )
        else:
            await update.message.reply_text(f"{input.capitalize()}: {result:.2f} €")

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None:
            return
        result = await self._crypto_api_service.list_top_crypto_currencies(amount=10)
        message = "Top 10 Cryptocurrencies by Market Cap:\n\n"
        for coin in result:
            message += f"{coin.market_cap_rank}. {coin.name} ({coin.symbol.upper()})\n"
            message += f"   Price: {coin.current_price:.2f} €\n"
            message += f"   Market Cap: {coin.market_cap:,} €\n"
            message += f"   Index ID: {coin.id}\n\n"
        await update.message.reply_text(message)

    async def add_fav_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user is None or update.message is None:
            return
        if context.args is None or not context.args:
            await update.message.reply_text("Please provide a cryptocurrency name.")
            return
        user_id = update.effective_user.id
        input_crypto = context.args[0].lower()
        answer = self._favorites_service.add_favorite(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
            input_crypto=input_crypto,
        )
        await update.message.reply_text(answer)

    async def remove_fav_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user is None or update.message is None:
            return
        if context.args is None or not context.args:
            await update.message.reply_text("Please provide a cryptocurrency name.")
            return
        user_id: str = str(update.effective_user.id)
        input_crypto = context.args[0].lower()
        answer = self._favorites_service.remove_favorite(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=user_id,
            input_crypto=input_crypto,
        )
        await update.message.reply_text(answer)

    async def list_favs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user is None or update.message is None:
            return
        user_id = update.effective_user.id
        answer = await self._favorites_service.list_favorites(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
        )
        await update.message.reply_text(answer)

    async def drop_favs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user is None or update.message is None:
            return
        user_id = update.effective_user.id
        answer = self._favorites_service.drop_favorites(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
        )
        await update.message.reply_text(answer)
