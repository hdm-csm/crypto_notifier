from typing import TYPE_CHECKING
from telegram import Update
from app.db import session_scope
from functools import wraps
from typing import Callable
from telegram.ext import ContextTypes
import logging
from app.utils.exceptions import AccountNotFoundOrCreatedException

if TYPE_CHECKING:
    from app.bots.telegram.modules.base_module import BaseModule


def with_session_and_account(func: Callable) -> Callable:
    """Decorator that provides db_session and account to command handlers."""

    @wraps(func)
    async def wrapper(
        self: "BaseModule", update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.effective_user is None or update.message is None:
            return
        user_id = update.effective_user.id
        with session_scope() as db_session:
            try:
                account = self._account_lookup_service.find_or_create_account(
                    db_session=db_session,
                    platform_type=self.PLATFORM_TYPE,
                    platform_user_id=str(user_id),
                )
            except AccountNotFoundOrCreatedException as e:
                logging.exception(str(e))
                await update.message.reply_text("⚠️ Account not found for user.")
                return

            # TODO: Do we need additional error handling here ?
            # try:
            #     await func(self, update, context, db_session, account)
            # except Exception as e:
            #     logging.error(f"Command error in {func.__name__}: {e}", exc_info=True)
            #     # TODO: Return command in error message ?
            #     await update.message.reply_text(f"❌ An error occurred: {str(e)}")
            await func(self, update, context, db_session, account)

    return wrapper
