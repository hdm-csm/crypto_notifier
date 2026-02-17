from app.bots.telegram.decorators import with_session_and_account
from app.bots.telegram.modules.base import AccountModule
from app.models.schemas import Account
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.utils.command_constants import (
    COMMAND_INDEX,
    COMMAND_LIST,
)
from app.utils.exceptions import MissingCommandArguments
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
from sqlalchemy.orm import Session


class CryptoInfoModule(AccountModule):

    def __init__(
        self,
        app: Application,
        account_lookup_service: AccountLookupService,
        crypocurrency_service: CryptoCurrencyService,
        crypto_api_service: CryptoApiService,
    ):
        super().__init__(app, account_lookup_service)
        self._crypto_currency_service = crypocurrency_service
        self._crypto_api_service = crypto_api_service

    def register(self):
        self._app.add_handler(CommandHandler(COMMAND_INDEX, self.index_command, block=False))
        self._app.add_handler(CommandHandler(COMMAND_LIST, self.list_command, block=False))

    @with_session_and_account
    async def index_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return
        if not context.args:
            raise MissingCommandArguments(COMMAND_INDEX, "<cryptocurrency>")
        crypto_currency_input: str = context.args[0]
        cryptocurrency = await self._crypto_currency_service.find_by_name_or_symbol(
            db_session, crypto_currency_input
        )
        if not cryptocurrency or not cryptocurrency.symbol:
            await update.message.reply_text(
                f"❌ Cryptocurrency '{crypto_currency_input}' not found. Please check the name or symbol and try again."
            )
            return
        vs_currency_symbol = "eur"
        if account and account.selected_vs_currency:
            vs_currency_symbol = account.selected_vs_currency.symbol.lower()
        answer: str = await self._crypto_api_service.get_index_2(
            crypto_symbol=cryptocurrency.symbol, vs_currency_symbol=vs_currency_symbol
        )
        if update.message:
            await update.message.reply_text(answer)

    @with_session_and_account
    async def list_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return
        vs_currency = "eur"
        if account and account.selected_vs_currency:
            vs_currency = account.selected_vs_currency.symbol.lower()
        answer: str = await self._crypto_api_service.list_top_crypto_currencies_str(
            amount=10, vs_currency=vs_currency
        )
        if update.message:
            await update.message.reply_text(answer)
