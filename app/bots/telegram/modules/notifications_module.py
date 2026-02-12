from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.bots.telegram.decorators import with_session_and_account
from app.bots.telegram.modules.base import AccountModule
from app.services.account_lookup_service import AccountLookupService
from app.services.notification_service import NotificationCheckResult, NotificationService
from app.models.schemas import Account
from app.models.enums import NotificationDirection
from sqlalchemy.orm import Session
import logging


class NotificationsModule(AccountModule):

    def __init__(
        self,
        app: Application,
        account_lookup_service: AccountLookupService,
        notification_service: NotificationService,
    ):
        super().__init__(app, account_lookup_service)
        self._notification_service = notification_service

    def register(self):
        self._app.add_handler(CommandHandler("add_notif", self.add_notif_command))
        self._app.add_handler(CommandHandler("add_notif", self.add_notif_command))
        self._app.add_handler(CommandHandler("list_notifs", self.list_notifs_command))
        self._app.add_handler(CommandHandler("remove_notif", self.remove_notif_command))
        self._app.add_handler(CommandHandler("drop_notifs", self.drop_notifs_command))

    def register_jobs(self):
        """Register background jobs. Called after app initialization."""
        # Schedule notification checking every 60 seconds
        if self._app.job_queue:
            self._app.job_queue.run_repeating(self.check_notifications, interval=60, first=1)

    async def check_notifications(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Check all notifications and send messages to users."""
        logging.info("[Telegram] - Checking notifications...")
        results: list[NotificationCheckResult] = (
            await self._notification_service.check_all_notifications()
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

        if context.args is None or len(context.args) < 4:
            await update.message.reply_text(
                "❌ Usage: `/add_notif <base_asset> <quote_asset> <above|below> <price>`\n"
                "Example: `/add_notif BTC USD above 50000`"
            )
            return

        base_asset = context.args[0].upper()
        quote_asset = context.args[1].upper()
        direction_str = context.args[2].lower()

        try:
            price = float(context.args[3])
        except ValueError:
            await update.message.reply_text("❌ Price must be a number.")
            return

        try:
            direction = (
                NotificationDirection.ABOVE
                if direction_str == "above"
                else NotificationDirection.BELOW
            )
        except ValueError:
            await update.message.reply_text("❌ Direction must be 'above' or 'below'.")
            return

        notification = self._notification_service.add_notification(
            session=db_session,
            account_id=account.id,
            base_asset=base_asset,
            quote_asset=quote_asset,
            direction=direction,
            target_price=price,
            already_hit=False,
        )

        await update.message.reply_text(
            f"✅ Notification added:\n{notification.base_asset}/{notification.quote_asset} {notification.direction.value} {notification.target_price}"
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
            await update.message.reply_text("No notifications set.")
            return

        message = "📢 Your notifications:\n\n"
        for notif in notifications:
            hit_indicator = "🔔" if notif.already_hit else "⏳"
            message += f"{hit_indicator} ID: {notif.id}\n"
            message += f"  {notif.base_asset}/{notif.quote_asset} {notif.direction.value} {notif.target_price}\n\n"

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
            await update.message.reply_text("Usage: /remove_notif <notification_id>")
            return

        try:
            notif_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Notification ID must be a number.")
            return

        removed = self._notification_service.remove_notification(
            session=db_session, notification_id=notif_id
        )

        if removed:
            await update.message.reply_text(f"✅ Notification {notif_id} removed.")
        else:
            await update.message.reply_text(f"❌ Notification {notif_id} not found.")

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
        await update.message.reply_text(f"✅ Dropped {count} notifications.")
