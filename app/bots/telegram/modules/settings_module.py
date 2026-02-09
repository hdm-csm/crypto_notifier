from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.bots.telegram.decorators import with_session_and_account
from app.bots.telegram.modules.base import AccountModule
from app.services.account_lookup_service import AccountLookupService
from app.models.schemas import Account
from sqlalchemy.orm import Session

from app.services.vs_currency_service import VsCurrencyService


class SettingsModule(AccountModule):

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        vs_currency_service: VsCurrencyService,
    ):
        super().__init__(account_lookup_service)
        self._vs_currency_service: VsCurrencyService = vs_currency_service

    def register(self, app: Application):
        app.add_handler(CommandHandler("get_vs", self._get_vs_currency_command))
        app.add_handler(CommandHandler("list_vs", self._list_vs_currencies))
        app.add_handler(CommandHandler("set_vs", self._set_vs_currency))

    @with_session_and_account
    async def _get_vs_currency_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return
        answer: str = self._vs_currency_service.get_vs_currency(account)
        await update.message.reply_text(answer)

    @with_session_and_account
    async def _list_vs_currencies(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return
        answer: str = self._vs_currency_service.list_supported_vs_currencies(db_session)
        await update.message.reply_text(answer)

    @with_session_and_account
    async def _set_vs_currency(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        """Set preferred vs currency."""
        if update.message is None:
            return
        if context.args is None or not context.args:
            await update.message.reply_text("Please provide a vs currency name.")
            return
        input = context.args[0].lower()
        answer: str = self._vs_currency_service.set_vs_currency(db_session, account, input)
        await update.message.reply_text(answer)
