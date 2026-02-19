import logging
from sqlalchemy.orm import Session
from app.db import session_scope
from app.repository.notification_repository import NotificationRepository
from app.models.schemas import Notification
from app.models.enums import NotificationDirection, PlatformType
from typing import NamedTuple
from app.utils.exceptions import InvalidNotificationArguments

from app.services.crypto_api_service import CryptoApiService

logger = logging.getLogger(__name__)


class NotificationCheckResult(NamedTuple):
    """Result of checking a notification"""

    current_price: float
    user_platform_id: str
    message: str


class NotificationService:

    def __init__(
        self, notification_repository: NotificationRepository, crypto_api_service: CryptoApiService
    ):
        self._notification_repository = notification_repository
        self._crypto_api_service = crypto_api_service

    def validate_and_parse_notification_args(
        self, crypto_symbol: str, vs_symbol: str, direction: str, price: str
    ) -> tuple[str, str, NotificationDirection, float]:
        """
        Validate and parse notification arguments.
        Raises InvalidNotificationArguments if validation fails.
        Returns tuple of (crypto_symbol, vs_symbol, direction_enum, price_float)
        """
        usage_hint = (
            "Usage: `/add_notif <crypto_symbol> <vs_symbol> <above|below> <price>`\n"
            "Example: `/add_notif BTC USD above 50000`"
        )

        try:
            price_float = float(price)
        except ValueError:
            raise InvalidNotificationArguments("❌ Price must be a number.", usage_hint)

        direction_lower = direction.lower()
        if direction_lower not in ["above", "below"]:
            raise InvalidNotificationArguments(
                "❌ Direction must be 'above' or 'below'.", usage_hint
            )

        direction_enum = (
            NotificationDirection.ABOVE
            if direction_lower == "above"
            else NotificationDirection.BELOW
        )

        return crypto_symbol.upper(), vs_symbol.upper(), direction_enum, price_float

    def add_notification(
        self,
        session: Session,
        account_id: int,
        crypto_symbol: str,
        vs_symbol: str,
        direction: NotificationDirection,
        target_price: float,
        already_hit: bool = False,
    ) -> Notification:
        """Add a new notification for an account"""

        return self._notification_repository.add(
            session=session,
            account_id=account_id,
            crypto_symbol=crypto_symbol,
            vs_symbol=vs_symbol,
            direction=direction,
            target_price=target_price,
            already_hit=already_hit,
        )

    def remove_notification(self, session: Session, notification_id: int) -> bool:
        """Remove a notification by ID"""
        return self._notification_repository.remove(
            session=session, notification_id=notification_id
        )

    def list_notifications_for_account(
        self, session: Session, account_id: int
    ) -> list[Notification]:
        """List all notifications for a specific account"""
        return self._notification_repository.list_by_account(session=session, account_id=account_id)

    def list_all_notifications(self, session: Session) -> list[Notification]:
        """List all notifications in the system"""
        return self._notification_repository.list_all(session=session)

    def list_notifications_by_platform(
        self, session: Session, platform: PlatformType
    ) -> list[Notification]:
        """List all notifications for a specific platform"""
        return self._notification_repository.list_by_platform(session=session, platform=platform)

    def get_notification(self, session: Session, notification_id: int) -> Notification | None:
        """Get a specific notification by ID"""
        return self._notification_repository.get_by_id(
            session=session, notification_id=notification_id
        )

    def update_notification_already_hit(
        self, session: Session, notification_id: int, already_hit: bool
    ) -> bool:
        """Update the already_hit flag for a notification"""
        return self._notification_repository.update_already_hit(
            session=session, notification_id=notification_id, already_hit=already_hit
        )

    def check_and_process_notification(
        self, session: Session, notif: Notification, current_price: float
    ) -> NotificationCheckResult:
        """
        Check if notification criteria is met and update state if needed.
        Returns a result with message ready to send to user.
        """
        # Check if criteria is met
        criteria_met = False
        if notif.direction == NotificationDirection.ABOVE and current_price >= notif.target_price:
            criteria_met = True
        elif notif.direction == NotificationDirection.BELOW and current_price <= notif.target_price:
            criteria_met = True

        message = ""

        # Handle state transitions
        if not notif.already_hit and criteria_met:
            # Criteria just met - update and create message
            self.update_notification_already_hit(
                session=session, notification_id=notif.id, already_hit=True
            )
            logging.info(
                f"Notification triggered for {notif.crypto_symbol}/{notif.vs_symbol} "
                f"{notif.direction.value} {notif.target_price} (current: {current_price})"
            )
            message = (
                f"🔔 Alert — {notif.crypto_symbol}/{notif.vs_symbol}\n"
                f"{notif.direction.value.capitalize()} {notif.target_price} · Now: {current_price}  (ID: {notif.id})"
            )

        elif notif.already_hit and not criteria_met:
            # Criteria no longer met - reset the hit flag
            self.update_notification_already_hit(
                session=session, notification_id=notif.id, already_hit=False
            )
            logging.info(
                f"Notification reset for {notif.crypto_symbol}/{notif.vs_symbol} "
                f"(current: {current_price})"
            )

        return NotificationCheckResult(
            current_price=current_price,
            user_platform_id=notif.account.platform_user_id,
            message=message,
        )

    async def check_all_notifications(
        self, platform: PlatformType
    ) -> list[NotificationCheckResult]:
        """
        Check all notifications for a specific platform and process state changes.
        Fetches all prices in a single batch call for efficiency.
        Returns a list of results for notifications that were triggered or reset.
        """
        results = []
        with session_scope() as db_session:
            if self._crypto_api_service is None:
                logging.error("Crypto API service not set for notification checking")
                return []

            notifications = self.list_notifications_by_platform(
                session=db_session, platform=platform
            )
            if not notifications:
                return []

            # Build tickers list from all notifications (format: "BASE-QUOTE")
            tickers = [f"{notif.crypto_symbol}-{notif.vs_symbol}" for notif in notifications]

            # Fetch all prices in a single call
            ticker_results = await self._crypto_api_service.fetch_ticker_prices(tickers)

            # Process each notification with its corresponding price
            for notif in notifications:
                try:
                    ticker_key = f"{notif.crypto_symbol}-{notif.vs_symbol}"
                    ticker_result = ticker_results.get(ticker_key)

                    # Skip if price data not found
                    if not ticker_result or not ticker_result.found or ticker_result.price is None:
                        logging.warning(f"Could not fetch price for {ticker_key}")
                        continue

                    current_price = ticker_result.price
                    result = self.check_and_process_notification(
                        session=db_session, notif=notif, current_price=current_price
                    )
                    if result.message:
                        results.append(result)
                except Exception as e:
                    logging.error(f"Error checking notification {notif.id}: {e}")

        return results
