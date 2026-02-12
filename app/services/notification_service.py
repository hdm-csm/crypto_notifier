import logging
from sqlalchemy.orm import Session
from app.db import session_scope
from app.repository.notification_repository import NotificationRepository
from app.models.schemas import Notification
from app.models.enums import NotificationDirection
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
        self, base_asset: str, quote_asset: str, direction: str, price: str
    ) -> tuple[str, str, NotificationDirection, float]:
        """
        Validate and parse notification arguments.
        Raises InvalidNotificationArguments if validation fails.
        Returns tuple of (base_asset, quote_asset, direction_enum, price_float)
        """
        usage_hint = (
            "Usage: `/add_notif <base_asset> <quote_asset> <above|below> <price>`\n"
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

        return base_asset.upper(), quote_asset.upper(), direction_enum, price_float

    def add_notification(
        self,
        session: Session,
        account_id: int,
        base_asset: str,
        quote_asset: str,
        direction: NotificationDirection,
        target_price: float,
        already_hit: bool = False,
    ) -> Notification:
        """Add a new notification for an account"""
        return self._notification_repository.add(
            session=session,
            account_id=account_id,
            base_asset=base_asset,
            quote_asset=quote_asset,
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
                f"Notification triggered for {notif.base_asset}/{notif.quote_asset} "
                f"{notif.direction.value} {notif.target_price} (current: {current_price})"
            )
            message = (
                f"🔔 *Notification Alert (ID: {notif.id})*\n\n"
                f"{notif.base_asset}/{notif.quote_asset} has gone {notif.direction.value}\n"
                f"Target: {notif.target_price}\n"
                f"Current Price: *{current_price}*\n"
            )

        elif notif.already_hit and not criteria_met:
            # Criteria no longer met - reset the hit flag
            self.update_notification_already_hit(
                session=session, notification_id=notif.id, already_hit=False
            )
            logging.info(
                f"Notification reset for {notif.base_asset}/{notif.quote_asset} "
                f"(current: {current_price})"
            )

        return NotificationCheckResult(
            current_price=current_price,
            user_platform_id=notif.account.platform_user_id,
            message=message,
        )

    async def check_all_notifications(self) -> list[NotificationCheckResult]:
        """
        Check all notifications and process state changes.
        Returns a list of results for notifications that were triggered or reset.
        """
        results = []
        with session_scope() as db_session:
            if self._crypto_api_service is None:
                logging.error("Crypto API service not set for notification checking")
                return []
            notifications = self.list_all_notifications(session=db_session)
            for notif in notifications:
                try:
                    current_price = await self._crypto_api_service.get_notification_index(
                        base_asset=notif.base_asset, quote_asset=notif.quote_asset
                    )
                    if current_price is None:
                        logging.warning(
                            f"Could not fetch price for {notif.base_asset}/{notif.quote_asset}"
                        )
                        continue
                    result = self.check_and_process_notification(
                        session=db_session, notif=notif, current_price=current_price
                    )
                    if result.message:
                        results.append(result)
                except Exception as e:
                    logging.error(f"Error checking notification {notif.id}: {e}")
        return results
