from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.bots.telegram.decorators import with_session_and_account
from app.bots.telegram.modules.base import TelegramModule
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.models.schemas import Account
from sqlalchemy.orm import Session

from app.services.fiat_currency_service import FiatCurrencyService


class SettingsModule(TelegramModule):
    PLATFORM_TYPE = PlatformType.TELEGRAM

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        _fiat_currency_service: FiatCurrencyService,
    ):
        self._fiat_currency_service: FiatCurrencyService = _fiat_currency_service
        super().__init__(account_lookup_service)

    def register(self, app: Application):
        app.add_handler(CommandHandler("get_fiat", self._get_fiat_currency_command))
        app.add_handler(CommandHandler("list_fiat", self._list_fiat_currencies))
        app.add_handler(CommandHandler("set_fiat", self._set_fiat_currency))

    @with_session_and_account
    async def _get_fiat_currency_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        answer: str = self._fiat_currency_service.get_fiat_currency(account)
        await update.message.reply_text(answer)

    @with_session_and_account
    async def _list_fiat_currencies(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        answer: str = self._fiat_currency_service.list_supported_fiat_currencies(db_session)
        await update.message.reply_text(answer)

    @with_session_and_account
    async def _set_fiat_currency(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        """Set preferred fiat currency."""
        # user_id: str = str(ctx.author.id)
        # answer: str = self._fiat_currency_service.set_fiat_currency(
        #     platform_type=self.PLATFORM_TYPE,
        #     platform_user_id=user_id,
        #     input=input,
        # )
        # await ctx.send(answer)
        input = context.args[0].lower()
        answer: str = self._fiat_currency_service.set_fiat_currency(db_session, account, input)
        await update.message.reply_text(answer)
