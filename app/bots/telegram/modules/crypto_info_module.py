from app.bots.telegram.decorators import with_session_and_account
from app.bots.telegram.modules.base import AccountModule
from app.models.schemas import Account
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
from sqlalchemy.orm import Session


class CryptoInfoModule(AccountModule):

    def __init__(
        self,
        app: Application,
        account_lookup_service: AccountLookupService,
        crypto_api_service: CryptoApiService,
    ):
        super().__init__(app, account_lookup_service)
        self._crypto_api_service = crypto_api_service

    def register(self):
        self._app.add_handler(CommandHandler("index", self.index_command, block=False))
        self._app.add_handler(CommandHandler("list", self.list_command, block=False))

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
            await update.message.reply_text(
                "Please provide a cryptocurrency name. Usage: /index bitcoin"
            )
            return
        crypto_currency_input: str = context.args[0]
        vs_currency = "eur"
        if account and account.selected_vs_currency:
            vs_currency = account.selected_vs_currency.short_name.lower()
        answer: str = await self._crypto_api_service.get_index_str(
            crypto_currency_input=crypto_currency_input, vs_currency=vs_currency
        )
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
            vs_currency = account.selected_vs_currency.short_name.lower()
        answer: str = await self._crypto_api_service.list_top_crypto_currencies_str(
            amount=10, vs_currency=vs_currency
        )
        await update.message.reply_text(answer)
