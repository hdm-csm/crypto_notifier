from discord.ext import commands
from app.bots.discord.cogs.base import AccountCog
from app.bots.discord.custom_bot import CustomDiscordBot
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.notification_service import NotificationCheckResult, NotificationService
from app.services.crypto_api_service import CryptoApiService
from app.bots.discord.custom_context import CustomContext
from app.utils.command_constants import (
    COMMAND_ADD_NOTIF,
    COMMAND_LIST_NOTIFS,
    COMMAND_REMOVE_NOTIF,
    COMMAND_DROP_NOTIFS,
)
from discord.ext import tasks
import discord
import logging


class NotificationsCog(AccountCog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        notification_service: NotificationService,
        crypto_api_service: CryptoApiService,
        bot: CustomDiscordBot,
    ):
        super().__init__(account_lookup_service)
        self._notification_service = notification_service
        self._crypto_api_service = crypto_api_service
        self._bot = bot
        self.check_notifications.start()

    def cog_unload(self):
        self.check_notifications.cancel()

    @tasks.loop(minutes=1.0)
    async def check_notifications(self):
        results: list[NotificationCheckResult] = (
            await self._notification_service.check_all_notifications()
        )
        for result in results:
            try:
                if self._bot is None:
                    logging.error("Bot not available for sending notifications")
                    continue
                user = await self._bot.fetch_user(int(result.user_platform_id))
                await user.send(result.message)
                logging.info(f"Sent notification message to user {result.user_platform_id}")
            except discord.NotFound:
                logging.warning(
                    f"User {result.user_platform_id} not found or no longer has DM access"
                )
            except discord.Forbidden:
                logging.warning(
                    f"Cannot send DM to user {result.user_platform_id}: permission denied or DMs disabled"
                )
            except Exception as e:
                logging.error(f"Failed to send DM to user {result.user_platform_id}: {e}")

    @check_notifications.before_loop
    async def before_check_notifications(self):
        print("waiting...")
        await self._bot.wait_until_ready()

    @commands.command(name=COMMAND_ADD_NOTIF)
    async def _add_notif(
        self,
        ctx: CustomContext,
        base_asset: str,
        quote_asset: str,
        direction: str,
        target_price: str,
    ) -> None:
        """Add a notification: /add_notif BTC USD above 50000"""
        base_asset, quote_asset, direction_enum, price_float = (
            self._notification_service.validate_and_parse_notification_args(
                base_asset=base_asset,
                quote_asset=quote_asset,
                direction=direction,
                price=target_price,
            )
        )

        notification = self._notification_service.add_notification(
            session=ctx.db_session,
            account_id=ctx.account.id,
            base_asset=base_asset,
            quote_asset=quote_asset,
            direction=direction_enum,
            target_price=price_float,
            already_hit=False,
        )

        await ctx.send(
            f"✅ Notification added:\n{notification.base_asset}/{notification.quote_asset} {notification.direction.value} {notification.target_price}"
        )

    @commands.command(name=COMMAND_LIST_NOTIFS)
    async def _list_notifs(self, ctx: CustomContext) -> None:
        """List all your notifications."""
        notifications = self._notification_service.list_notifications_for_account(
            session=ctx.db_session, account_id=ctx.account.id
        )

        if not notifications:
            await ctx.send("No notifications set.")
            return

        message = "📢 Your notifications:\n\n"
        for notif in notifications:
            hit_indicator = "🔔" if notif.already_hit else "⏳"
            message += f"{hit_indicator} ID: {notif.id}\n"
            message += f"  {notif.base_asset}/{notif.quote_asset} {notif.direction.value} {notif.target_price}\n\n"

        await ctx.send(message)

    @commands.command(name=COMMAND_REMOVE_NOTIF)
    async def _remove_notif(self, ctx: CustomContext, notification_id: str) -> None:
        """Remove a notification by ID: /remove_notif 5"""
        try:
            notif_id = int(notification_id)
        except ValueError:
            await ctx.send("❌ Notification ID must be a number.")
            return

        removed = self._notification_service.remove_notification(
            session=ctx.db_session, notification_id=notif_id
        )

        if removed:
            await ctx.send(f"✅ Notification {notif_id} removed.")
        else:
            await ctx.send(f"❌ Notification {notif_id} not found.")

    @commands.command(name=COMMAND_DROP_NOTIFS)
    async def _drop_notifs(self, ctx: CustomContext) -> None:
        """Remove all your notifications."""
        notifications = self._notification_service.list_notifications_for_account(
            session=ctx.db_session, account_id=ctx.account.id
        )

        for notif in notifications:
            self._notification_service.remove_notification(
                session=ctx.db_session, notification_id=notif.id
            )

        count = len(notifications)
        await ctx.send(f"✅ Dropped {count} notifications.")
