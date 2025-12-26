import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ApplicationBuilder
from app.repository.account_repository import AccountRepository
from app.repository.favorite_repository import FavoriteRepository
from app.services.bot_service import BotService
from app.services.crypto_api_service import CryptoApiService
from app.models import PlatformType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

class TelegramBot:

    PLATFORM_TYPE = PlatformType.Telegram

    def __init__(
            self, 
            token: str, 
            crypto_api_service: CryptoApiService,
            account_repository: AccountRepository,
            favorite_repository: FavoriteRepository,
            bot_service: BotService):
        self.token = token
        self.crypto_api_service = crypto_api_service
        self.account_repository = account_repository
        self.favorite_repository = favorite_repository
        self._bot_service = bot_service
        
        self.app = ApplicationBuilder().token(token).build()
        self.app.add_handler(CommandHandler("index", self.index_command, block=False))
        self.app.add_handler(CommandHandler("list", self.list_command, block=False))
        self.app.add_handler(CommandHandler("add_fav", self.save_fav_command, block=False))

    async def start(self):
        """Start the Telegram bot."""
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(
            poll_interval=0.0,
            timeout=60,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        logging.info("TelegramBot has started!")

    async def stop(self):
        """Stop the Telegram bot."""
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()

    async def index_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Please provide a cryptocurrency name. Usage: /index bitcoin")
            return
        input = context.args[0]
        result = await self.crypto_api_service.get_index(input)
        if result is None:
            await update.message.reply_text(f"Could not find price for {input}")
        else:
            await update.message.reply_text(f"{input.capitalize()}: {result:.2f} €")

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        result = await self.crypto_api_service.list_top_crypto_currencies(amount=10)
        message = "Top 10 Cryptocurrencies by Market Cap:\n\n"
        for coin in result:
            message += f"{coin.market_cap_rank}. {coin.name} ({coin.symbol.upper()})\n"
            message += f"   Price: {coin.current_price:.2f} €\n"
            message += f"   Market Cap: {coin.market_cap:,} €\n\n"
        await update.message.reply_text(message)

    async def save_fav_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        input_crypto = context.args[0].lower()
        answer = self._bot_service.add_favorite(
            platformType=self.PLATFORM_TYPE,
            user_id=str(user_id),
            input_crypto=input_crypto
        )
        await update.message.reply_text(answer)
        return
    
        #     return
        # account = self.account_repository.find_by_platform_and_id(
        #     platform=self.PLATFORM_TYPE,
        #     platform_id=str(user_id)
        # )
        # if account is None:
        #     account = self.account_repository.create(
        #         platform=self.PLATFORM_TYPE,
        #         platformId=str(user_id)
        #     )
        # cryptocurrency = self.cryptocurrency_repository.find_by_name_or_symbol(input_crypto)
        # if cryptocurrency is None:
        #     return False

        # if not account:
        #     await update.message.reply_text(f"⚠️ Could not find or create account for user ID {user_id}.")
        #     return

        # if not cryptocurrency:
        #     await update.message.reply_text(f"⚠️ Cryptocurrency '{input_crypto}' not found. Please check the name/symbol and try again.")
        #     return

        # success = self.favorite_repository.add_favorite(
        #     account=account,
        #     crypto=cryptocurrency
        # )
        
        # if success:
        #     await update.message.reply_text(f"✅ Saved {input_crypto} as your favorite cryptocurrency!")
        # else:
        #     await update.message.reply_text(f"⚠️ {input_crypto} is already in your favorites.")
