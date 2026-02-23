from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.bots.telegram.decorators import with_session_and_account
from app.bots.telegram.modules.base_module import BaseModule
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.notification_service import NotificationCheckResult, NotificationService
from app.models.schemas import Account, Notification
from app.models.enums import NotificationDirection, PlatformType
from app.services.vs_currency_service import VsCurrencyService
from app.bots.constants.commands import (
    COMMAND_ADD_NOTIF,
    COMMAND_LIST_NOTIFS,
    COMMAND_REMOVE_NOTIF,
    COMMAND_DROP_NOTIFS,
)
from app.utils.exceptions import MissingCommandArguments
from sqlalchemy.orm import Session
import logging


class NotificationsModule(BaseModule):

    def __init__(
        self,
        app: Application,
        account_lookup_service: AccountLookupService,
        notification_service: NotificationService,
        crypto_currency_service: CryptoCurrencyService,
        vs_currency_service: VsCurrencyService,
    ):
        super().__init__(app, account_lookup_service)
        self._notification_service = notification_service
        self._crypto_currency_service = crypto_currency_service
        self._vs_currency_service = vs_currency_service

    def register(self):
        self._app.add_handler(CommandHandler(COMMAND_ADD_NOTIF, self.add_notif_command))
        self._app.add_handler(CommandHandler(COMMAND_ADD_NOTIF, self.add_notif_command))
        self._app.add_handler(CommandHandler(COMMAND_LIST_NOTIFS, self.list_notifs_command))
        self._app.add_handler(CommandHandler(COMMAND_REMOVE_NOTIF, self.remove_notif_command))
        self._app.add_handler(CommandHandler(COMMAND_DROP_NOTIFS, self.drop_notifs_command))

    def register_jobs(self):
        """Register background jobs. Called after app initialization."""
        # Schedule notification checking every 10 seconds
        if self._app.job_queue:
            self._app.job_queue.run_repeating(self.check_notifications, interval=10, first=1)

    async def check_notifications(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Check all notifications and send messages to users."""
        logging.info("[Telegram] - Checking notifications...")
        results: list[NotificationCheckResult] = (
            await self._notification_service.check_all_notifications(PlatformType.TELEGRAM)
        )
        for result in results:
            try:
                if self._app is None:
                    logging.error("Telegram app not available for sending notifications")
                    continue
                await context.bot.send_message(chat_id=result.user_platform_id, text=result.message)
                logging.info(f"Sent notification message to user {result.user_platform_id}")
            except Exception as e:
                logging.error(
                    f"[Telegram - check_notifications()]:\n Failed to send message to user {result.user_platform_id}: {e}"
                )
        logging.info("[Telegram] - Finished checking notifications.")

    @with_session_and_account
    async def add_notif_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return

        if not context.args or len(context.args) < 4:
            raise MissingCommandArguments(
                COMMAND_ADD_NOTIF, "<crypto_symbol> <vs_symbol> <above|below> <price>"
            )

        crypto_symbol = context.args[0].upper()  # check if cur -> get symbol
        vs_symbol = context.args[1].upper()  # check if vs -> get symbol
        direction_str = context.args[2].lower()

        crypto_currency = self._crypto_currency_service.find_by_name_or_symbol(
            db_session, crypto_symbol
        )
        if not crypto_currency or not crypto_currency.symbol:
            await update.message.reply_text(
                f"❌ Cryptocurrency '{crypto_symbol}' not found. Please check the name or symbol and try again."
            )
            return

        vs_currency = self._vs_currency_service.find_by_symbol_or_name(db_session, vs_symbol)
        if not vs_currency or not vs_currency.symbol:
            await update.message.reply_text(
                f"❌ Quote currency '{vs_symbol}' not found. Please check the name or symbol and try again."
            )
            return

        try:
            price = float(context.args[3])
        except ValueError:
            if update.message:
                await update.message.reply_text("❌ Price must be a number.")
            return

        try:
            direction = (
                NotificationDirection.ABOVE
                if direction_str == "above"
                else NotificationDirection.BELOW
            )
        except ValueError:
            if update.message:
                await update.message.reply_text("❌ Direction must be 'above' or 'below'.")
            return

        notification: Notification = self._notification_service.add_notification(
            session=db_session,
            account_id=account.id,
            crypto_symbol=crypto_currency.symbol.upper(),
            vs_symbol=vs_currency.symbol.upper(),
            direction=direction,
            target_price=price,
            already_hit=False,
        )

        if update.message:
            await update.message.reply_text(
                f"✅ Notification set: {notification.crypto_symbol}/{notification.vs_symbol} {notification.direction.value} {notification.target_price}  (ID: {notification.id})"
            )

    @with_session_and_account
    async def list_notifs_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return

        notifications = self._notification_service.list_notifications_for_account(
            session=db_session, account_id=account.id
        )

        if not notifications:
            if update.message:
                await update.message.reply_text("ℹ️ No notifications set.")
            return

        message = f"Notifications ({len(notifications)})\n\n"
        for notif in notifications:
            status = "🔔" if notif.already_hit else "⏳"
            message += f"{status} {notif.crypto_symbol}/{notif.vs_symbol} {notif.direction.value} {notif.target_price}  (ID: {notif.id})\n"

        if update.message:
            await update.message.reply_text(message)

    @with_session_and_account
    async def remove_notif_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return

        if context.args is None or not context.args:
            if update.message:
                await update.message.reply_text("Usage: /remove_notif <notification_id>")
            return

        try:
            notif_id = int(context.args[0])
        except ValueError:
            if update.message:
                await update.message.reply_text("❌ Notification ID must be a number.")
            return

        removed = self._notification_service.remove_notification(
            session=db_session, notification_id=notif_id
        )

        if removed:
            if update.message:
                await update.message.reply_text(f"✅ Notification {notif_id} removed.")
        else:
            if update.message:
                await update.message.reply_text(f"❌ No notification with ID {notif_id}.")

    @with_session_and_account
    async def drop_notifs_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db_session: Session,
        account: Account,
    ) -> None:
        if update.message is None:
            return

        notifications = self._notification_service.list_notifications_for_account(
            session=db_session, account_id=account.id
        )

        for notif in notifications:
            self._notification_service.remove_notification(
                session=db_session, notification_id=notif.id
            )

        count = len(notifications)
        if update.message:
            await update.message.reply_text(f"✅ Removed {count} notification(s).")
