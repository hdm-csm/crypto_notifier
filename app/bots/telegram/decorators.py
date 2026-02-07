from telegram import Update
from app.bots.telegram.telegram_bot import TelegramBot
from app.db import session_scope
from functools import wraps
from typing import Callable
from telegram.ext import ContextTypes

from app.utils.exceptions import AccountNotFoundOrCreatedException


def with_session_and_account(func: Callable) -> Callable:
    """Decorator that provides db_session and account to command handlers."""

    @wraps(func)
    async def wrapper(
        self: "TelegramBot", update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.effective_user is None or update.message is None:
            return
        user_id = update.effective_user.id
        with session_scope() as db_session:
            try:
                account = self._favorites_service._account_lookup_service.find_or_create_account(
                    session=db_session,
                    platform_type=self.PLATFORM_TYPE,
                    platform_user_id=str(user_id),
                )
            except AccountNotFoundOrCreatedException as e:
                logging.exception(str(e))
                await update.message.reply_text("⚠️ Account not found for user.")
                return

            try:
                await func(self, update, context, db_session, account)
            except Exception as e:
                logging.error(f"Command error in {func.__name__}: {e}", exc_info=True)
                await update.message.reply_text(f"❌ An error occurred: {str(e)}")

    return wrapper
