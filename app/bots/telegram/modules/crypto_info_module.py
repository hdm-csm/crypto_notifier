from app.bots.telegram.modules.base import TelegramModule
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update


class CryptoInfoModule(TelegramModule):

    def __init__(
        self, account_lookup_service: AccountLookupService, crypto_api_service: CryptoApiService
    ):
        self._crypto_api_service = crypto_api_service
        super().__init__(account_lookup_service)

    def register(self, app: Application):
        app.add_handler(CommandHandler("index", self.index_command, block=False))
        app.add_handler(CommandHandler("list", self.list_command, block=False))

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
