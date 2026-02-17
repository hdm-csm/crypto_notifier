from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.bots.telegram.decorators import with_session_and_account
from app.bots.telegram.modules.base import AccountModule
from app.services.account_lookup_service import AccountLookupService
from app.services.favorites_service import FavoritesService
from app.models.schemas import Account
from app.utils.command_constants import (
    COMMAND_ADD_FAV,
    COMMAND_LIST_FAVS,
    COMMAND_REMOVE_FAV,
    COMMAND_DROP_FAVS,
)
from app.utils.exceptions import MissingCommandArguments
from sqlalchemy.orm import Session


class FavoritesModule(AccountModule):

    def __init__(
        self,
        app: Application,
        account_lookup_service: AccountLookupService,
        favorites_service: FavoritesService,
    ):
        super().__init__(app, account_lookup_service)
        self._favorites_service = favorites_service

    def register(self):
        self._app.add_handler(CommandHandler(COMMAND_ADD_FAV, self.add_fav_command))
        self._app.add_handler(CommandHandler(COMMAND_LIST_FAVS, self.list_favs_command))
        self._app.add_handler(CommandHandler(COMMAND_REMOVE_FAV, self.remove_fav_command))
        self._app.add_handler(CommandHandler(COMMAND_DROP_FAVS, self.drop_favs_command))

    @with_session_and_account
    async def add_fav_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if not context.args:
            raise MissingCommandArguments(COMMAND_ADD_FAV, "<cryptocurrency>")
        input_crypto = context.args[0]
        answer = self._favorites_service.add_favorite(
            db_session=db_session, account=account, input_crypto=input_crypto
        )
        if update.message:
            await update.message.reply_text(answer)

    @with_session_and_account
    async def remove_fav_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if not context.args:
            raise MissingCommandArguments(COMMAND_REMOVE_FAV, "<cryptocurrency>")
        input_crypto = context.args[0].lower()
        answer = self._favorites_service.remove_favorite(
            db_session=db_session, account=account, input_crypto=input_crypto
        )
        if update.message:
            await update.message.reply_text(answer)

    @with_session_and_account
    async def list_favs_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return
        answer = await self._favorites_service.list_favorites(account=account)
        if update.message:
            await update.message.reply_text(answer)

    @with_session_and_account
    async def drop_favs_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return
        answer = self._favorites_service.drop_favorites(account=account)
        if update.message:
            await update.message.reply_text(answer)
