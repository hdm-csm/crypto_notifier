from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.bots.telegram.decorators import with_session_and_account
from app.bots.telegram.modules.base import AccountModule
from app.services.account_lookup_service import AccountLookupService
from app.models.schemas import Account
from app.utils.command_constants import (
    COMMAND_GET_VS,
    COMMAND_LIST_VS,
    COMMAND_SET_VS,
)
from app.utils.exceptions import MissingCommandArguments
from sqlalchemy.orm import Session

from app.services.vs_currency_service import VsCurrencyService


class SettingsModule(AccountModule):

    def __init__(
        self,
        app: Application,
        account_lookup_service: AccountLookupService,
        vs_currency_service: VsCurrencyService,
    ):
        super().__init__(app, account_lookup_service)
        self._vs_currency_service: VsCurrencyService = vs_currency_service

    def register(self):
        self._app.add_handler(CommandHandler(COMMAND_GET_VS, self._get_vs_currency_command))
        self._app.add_handler(CommandHandler(COMMAND_LIST_VS, self._list_vs_currencies))
        self._app.add_handler(CommandHandler(COMMAND_SET_VS, self._set_vs_currency))

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
        if update.message:
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
        if update.message:
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
        if not context.args:
            raise MissingCommandArguments(COMMAND_SET_VS, "<currency>")
        input = context.args[0].lower()
        answer: str = self._vs_currency_service.set_vs_currency(db_session, account, input)
        if update.message:
            await update.message.reply_text(answer)
