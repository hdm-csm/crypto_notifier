import logging
from sqlalchemy.orm import Session
from app.models.schemas import Notification, Account
from app.models.enums import NotificationDirection, PlatformType

logger = logging.getLogger(__name__)


class NotificationRepository:

    def add(
        self,
        session: Session,
        account_id: int,
        crypto_symbol: str,
        vs_symbol: str,
        direction: NotificationDirection,
        target_price: float,
        already_hit: bool = False,
    ) -> Notification:
        """Create and add a new notification"""
        new_notification = Notification(
            account_id=account_id,
            crypto_symbol=crypto_symbol,
            vs_symbol=vs_symbol,
            direction=direction,
            target_price=target_price,
            already_hit=already_hit,
        )
        session.add(new_notification)
        session.flush()
        session.refresh(new_notification)
        logging.info(
            f"Created notification for account {account_id}: {crypto_symbol}/{vs_symbol} {direction.value} {target_price}"
        )
        return new_notification

    def remove(self, session: Session, notification_id: int) -> bool:
        """Remove a notification by ID. Returns True if deleted, False if not found"""
        notification = (
            session.query(Notification).filter(Notification.id == notification_id).first()
        )
        if notification:
            session.delete(notification)
            session.flush()
            logging.info(f"Deleted notification {notification_id}")
            return True
        logging.warning(f"Notification {notification_id} not found")
        return False

    def list_by_account(self, session: Session, account_id: int) -> list[Notification]:
        """List all notifications for a specific account"""
        return session.query(Notification).filter(Notification.account_id == account_id).all()

    def list_all(self, session: Session) -> list[Notification]:
        """List all notifications"""
        return session.query(Notification).all()

    def list_by_platform(self, session: Session, platform: PlatformType) -> list[Notification]:
        """List all notifications for a specific platform"""
        return session.query(Notification).join(Account).filter(Account.platform == platform).all()

    def get_by_id(self, session: Session, notification_id: int) -> Notification | None:
        """Get a notification by ID"""
        return session.query(Notification).filter(Notification.id == notification_id).first()

    def update_already_hit(self, session: Session, notification_id: int, already_hit: bool) -> bool:
        """Update the already_hit flag for a notification. Returns True if updated, False if not found"""
        notification = (
            session.query(Notification).filter(Notification.id == notification_id).first()
        )
        if notification:
            notification.already_hit = already_hit
            session.flush()
            logging.info(f"Updated notification {notification_id} already_hit to {already_hit}")
            return True
        logging.warning(f"Notification {notification_id} not found")
        return False
