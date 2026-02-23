from discord import app_commands
from app.bots.discord.cogs.base_cog import BaseCog
from app.bots.discord.custom.custom_bot import CustomDiscordBot
from app.bots.discord.utils.autocompletes import crypto_autocomplete, vs_currency_autocomplete
from app.models.enums import PlatformType
from app.services.notification_service import NotificationCheckResult, NotificationService
from app.services.crypto_api_service import CryptoApiService
from app.bots.discord.custom.custom_interaction import get_db_session, get_account
from app.bots.constants.commands import (
    COMMAND_ADD_NOTIF,
    COMMAND_LIST_NOTIFS,
    COMMAND_REMOVE_NOTIF,
    COMMAND_DROP_NOTIFS,
)
from discord.ext import tasks
import discord
import logging


class NotificationsCog(BaseCog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        bot: CustomDiscordBot,
        notification_service: NotificationService,
        crypto_api_service: CryptoApiService,
    ):
        super().__init__()
        self._bot = bot
        self._notification_service = notification_service
        self._crypto_api_service = crypto_api_service
        self.check_notifications_task.start()

    def cog_unload(self):
        self.check_notifications_task.cancel()

    @tasks.loop(minutes=1.0)
    async def check_notifications_task(self):
        await self.check_notifications()

    async def check_notifications(self):
        logging.info("[Discord] - Checking notifications...")
        results: list[NotificationCheckResult] = (
            await self._notification_service.check_all_notifications(PlatformType.DISCORD)
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
        logging.info("[Discord] - Finished checking notifications.")

    @check_notifications_task.before_loop
    async def before_check_notifications(self):
        print("waiting...")
        await self._bot.wait_until_ready()

    @app_commands.command(name=COMMAND_ADD_NOTIF, description="Add a price notification")
    @app_commands.describe(
        crypto_symbol="Cryptocurrency symbol",
        vs_symbol="Quote currency symbol",
        direction="Direction: 'above' or 'below'",
        target_price="Target price",
    )
    @app_commands.choices(
        direction=[
            app_commands.Choice(name="Above 📈", value="above"),
            app_commands.Choice(name="Below 📉", value="below"),
        ]
    )
    @app_commands.autocomplete(
        crypto_symbol=crypto_autocomplete, vs_symbol=vs_currency_autocomplete
    )
    async def _add_notif(
        self,
        interaction: discord.Interaction,
        crypto_symbol: str,
        vs_symbol: str,
        direction: str,
        target_price: float,  # Automatically forces the user to input a number
    ) -> None:
        """Add a notification for price changes."""
        db_session = get_db_session(interaction)
        account = get_account(interaction)
        crypto_symbol, vs_symbol, direction_enum, price_float = (
            self._notification_service.validate_and_parse_notification_args(
                crypto_symbol=crypto_symbol,
                vs_symbol=vs_symbol,
                direction=direction,
                price=target_price,
            )
        )
        crypto_currency = self._bot.crypto_currency_service.find_by_name_or_symbol(
            db_session, crypto_symbol
        )
        if not crypto_currency or not crypto_currency.symbol:
            await interaction.followup.send(
                f"❌ Cryptocurrency '{crypto_symbol}' not found. Please check the name or symbol and try again."
            )
            return
        vs_currency = self._bot.vs_currency_service.find_by_symbol_or_name(db_session, vs_symbol)
        if not vs_currency or not vs_currency.symbol:
            await interaction.followup.send(
                f"❌ Quote currency '{vs_symbol}' not found. Please check the name or symbol and try again."
            )
            return

        notification = self._notification_service.add_notification(
            session=db_session,
            account_id=account.id,
            crypto_symbol=crypto_currency.symbol.upper(),
            vs_symbol=vs_currency.symbol.upper(),
            direction=direction_enum,
            target_price=price_float,
            already_hit=False,
        )

        await interaction.followup.send(
            f"✅ Notification set: {notification.crypto_symbol}/{notification.vs_symbol} {notification.direction.value} {notification.target_price}  (ID: {notification.id})"
        )

    @app_commands.command(name=COMMAND_LIST_NOTIFS, description="List all your notifications")
    async def _list_notifs(self, interaction: discord.Interaction) -> None:
        """List all your notifications."""
        db_session = get_db_session(interaction)
        account = get_account(interaction)
        notifications = self._notification_service.list_notifications_for_account(
            session=db_session, account_id=account.id
        )

        if not notifications:
            await interaction.followup.send("ℹ️ No notifications set.")
            return

        message = f"Notifications ({len(notifications)})\n\n"
        for notif in notifications:
            status = "🔔" if notif.already_hit else "⏳"
            message += f"{status} {notif.crypto_symbol}/{notif.vs_symbol} {notif.direction.value} {notif.target_price}  (ID: {notif.id})\n"

        await interaction.followup.send(message)

    @app_commands.command(name=COMMAND_REMOVE_NOTIF, description="Remove a notification by ID")
    @app_commands.describe(notification_id="The notification ID to remove")
    async def _remove_notif(self, interaction: discord.Interaction, notification_id: str) -> None:
        """Remove a notification by ID."""
        db_session = get_db_session(interaction)
        try:
            notif_id = int(notification_id)
        except ValueError:
            await interaction.followup.send("❌ Notification ID must be a number.")
            return

        removed = self._notification_service.remove_notification(
            session=db_session, notification_id=notif_id
        )

        if removed:
            await interaction.followup.send(f"✅ Notification {notif_id} removed.")
        else:
            await interaction.followup.send(f"❌ No notification with ID {notif_id}.")

    @app_commands.command(name=COMMAND_DROP_NOTIFS, description="Remove all your notifications")
    async def _drop_notifs(self, interaction: discord.Interaction) -> None:
        """Remove all your notifications."""
        db_session = get_db_session(interaction)
        account = get_account(interaction)
        notifications = self._notification_service.list_notifications_for_account(
            session=db_session, account_id=account.id
        )

        for notif in notifications:
            self._notification_service.remove_notification(
                session=db_session, notification_id=notif.id
            )

        count = len(notifications)
        await interaction.followup.send(f"✅ Removed {count} notification(s).")
