from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.bots.telegram.decorators import with_session_and_account
from app.bots.telegram.modules.base import TelegramModule
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.favorites_service import FavoritesService
from app.models.schemas import Account
from sqlalchemy.orm import Session


class FavoritesModule(TelegramModule):
    PLATFORM_TYPE = PlatformType.TELEGRAM

    def __init__(
        self, account_lookup_service: AccountLookupService, favorites_service: FavoritesService
    ):
        super().__init__(account_lookup_service)
        self._favorites_service = favorites_service

    def register(self, app: Application):
        app.add_handler(CommandHandler("add_fav", self.add_fav_command))
        app.add_handler(CommandHandler("list_favs", self.list_favs_command))
        app.add_handler(CommandHandler("remove_fav", self.remove_fav_command))
        app.add_handler(CommandHandler("drop_favs", self.drop_favs_command))

    @with_session_and_account
    async def add_fav_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        # if update.effective_user is None or update.message is None:
        #     return
        if context.args is None or not context.args:
            await update.message.reply_text("Please provide a cryptocurrency name.")
            return
        input_crypto = context.args[0].lower()
        answer = self._favorites_service.add_favorite(
            db_session=db_session, account=account, input_crypto=input_crypto
        )
        await update.message.reply_text(answer)

    @with_session_and_account
    async def remove_fav_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        # if update.effective_user is None or update.message is None:
        #     return
        if context.args is None or not context.args:
            await update.message.reply_text("Please provide a cryptocurrency name.")
            return
        input_crypto = context.args[0].lower()
        answer = self._favorites_service.remove_favorite(
            db_session=db_session, account=account, input_crypto=input_crypto
        )
        await update.message.reply_text(answer)

    @with_session_and_account
    async def list_favs_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        # if update.effective_user is None or update.message is None:
        #     return
        answer = await self._favorites_service.list_favorites(account=account)
        await update.message.reply_text(answer)

    @with_session_and_account
    async def drop_favs_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        # if update.effective_user is None or update.message is None:
        #     return
        answer = self._favorites_service.drop_favorites(account=account)
        await update.message.reply_text(answer)
