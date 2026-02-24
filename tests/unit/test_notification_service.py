import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.notification_service import NotificationService
from app.models.enums import NotificationDirection, PlatformType
from app.models.schemas import Notification, Account
from app.models.dtos import CryptoPrice
from app.utils.exceptions import InvalidNotificationArguments


@pytest.fixture
def mock_notification_repository():
    return Mock()


@pytest.fixture
def mock_crypto_api_service():
    # Muss ein AsyncMock sein, da check_all_notifications await benutzt
    return AsyncMock()


@pytest.fixture
def mock_session():
    # Ein Mock für die SQLAlchemy Session
    return MagicMock()


@pytest.fixture
def notification_service(mock_notification_repository, mock_crypto_api_service):
    return NotificationService(
        notification_repository=mock_notification_repository,
        crypto_api_service=mock_crypto_api_service,
    )


@pytest.fixture
def sample_account():
    account = Account(platform=PlatformType.DISCORD, platform_user_id="123456789")
    account.id = 1
    return account


@pytest.fixture
def sample_notification(sample_account):
    notification = Notification()
    notification.id = 1
    notification.account_id = sample_account.id
    notification.account = sample_account
    notification.crypto_symbol = "BTC"
    notification.vs_symbol = "USD"
    notification.target_price = 50000.00
    notification.direction = NotificationDirection.ABOVE
    notification.already_hit = False
    return notification


class TestValidateAndParseNotificationArgs:
    """Tests für validate_and_parse_notification_args"""

    def test_valid_args_above_direction(self, notification_service):
        # Act
        c, v, d, p = notification_service.validate_and_parse_notification_args(
            crypto_symbol="btc", vs_symbol="usd", direction="above", price=50000.0
        )

        # Assert (Prüft auch das Upper-Casing)
        assert c == "BTC"
        assert v == "USD"
        assert d == NotificationDirection.ABOVE
        assert p == 50000.0

    def test_valid_args_below_direction(self, notification_service):
        # Act
        c, v, d, p = notification_service.validate_and_parse_notification_args(
            crypto_symbol="Eth", vs_symbol="Eur", direction="below", price=3000.50
        )

        # Assert
        assert c == "ETH"
        assert v == "EUR"
        assert d == NotificationDirection.BELOW
        assert p == 3000.50

    def test_invalid_direction_raises_exception(self, notification_service):
        # Act & Assert
        with pytest.raises(InvalidNotificationArguments) as exc:
            notification_service.validate_and_parse_notification_args(
                crypto_symbol="btc", vs_symbol="usd", direction="invalid", price=50000.0
            )
        assert "Direction must be 'above' or 'below'" in str(exc.value)


class TestAddNotification:
    """Tests für add_notification"""

    def test_add_notification_success(
        self, notification_service, mock_notification_repository, mock_session, sample_notification
    ):
        # Arrange
        mock_notification_repository.add.return_value = sample_notification

        # Act
        result = notification_service.add_notification(
            session=mock_session,
            account_id=1,
            crypto_symbol="BTC",
            vs_symbol="USD",
            direction=NotificationDirection.ABOVE,
            target_price=50000.00,
        )

        # Assert
        mock_notification_repository.add.assert_called_once_with(
            session=mock_session,
            account_id=1,
            crypto_symbol="BTC",
            vs_symbol="USD",
            direction=NotificationDirection.ABOVE,
            target_price=50000.00,
            already_hit=False,
        )
        assert result == sample_notification

    def test_add_notification_with_below_direction(
        self, notification_service, mock_notification_repository, mock_session, sample_notification
    ):
        # Arrange
        sample_notification.direction = NotificationDirection.BELOW
        mock_notification_repository.add.return_value = sample_notification

        # Act
        result = notification_service.add_notification(
            session=mock_session,
            account_id=1,
            crypto_symbol="BTC",
            vs_symbol="USD",
            direction=NotificationDirection.BELOW,
            target_price=45000.00,
        )

        # Assert
        assert result.direction == NotificationDirection.BELOW

    def test_add_notification_with_decimal_price(
        self, notification_service, mock_notification_repository, mock_session, sample_notification
    ):
        # Arrange
        sample_notification.target_price = 50000.12345
        mock_notification_repository.add.return_value = sample_notification

        # Act
        result = notification_service.add_notification(
            session=mock_session,
            account_id=1,
            crypto_symbol="BTC",
            vs_symbol="USD",
            direction=NotificationDirection.ABOVE,
            target_price=50000.12345,
        )

        # Assert
        assert result.target_price == 50000.12345


class TestRemoveNotification:
    """Tests für remove_notification"""

    def test_remove_notification_success(
        self, notification_service, mock_notification_repository, mock_session
    ):
        # Arrange
        mock_notification_repository.remove.return_value = True

        # Act
        result = notification_service.remove_notification(session=mock_session, notification_id=1)

        # Assert
        mock_notification_repository.remove.assert_called_once_with(
            session=mock_session, notification_id=1
        )
        assert result is True

    def test_remove_notification_not_found_returns_false(
        self, notification_service, mock_notification_repository, mock_session
    ):
        # Arrange
        mock_notification_repository.remove.return_value = False

        # Act
        result = notification_service.remove_notification(session=mock_session, notification_id=999)

        # Assert
        assert result is False

    def test_remove_notification_with_invalid_id_type(
        self, notification_service, mock_notification_repository, mock_session
    ):
        # Arrange
        mock_notification_repository.remove.side_effect = TypeError()

        # Act & Assert
        with pytest.raises(TypeError):
            notification_service.remove_notification(
                session=mock_session, notification_id="invalid"
            )


class TestListNotificationsForAccount:
    """Tests für list_notifications_for_account"""

    def test_list_notifications_returns_list(
        self, notification_service, mock_notification_repository, mock_session, sample_notification
    ):
        # Arrange
        notifications = [sample_notification]
        mock_notification_repository.list_by_account.return_value = notifications

        # Act
        result = notification_service.list_notifications_for_account(
            session=mock_session, account_id=1
        )

        # Assert
        mock_notification_repository.list_by_account.assert_called_once_with(
            session=mock_session, account_id=1
        )
        assert result == notifications

    def test_list_notifications_multiple_items(
        self, notification_service, mock_notification_repository, mock_session, sample_notification
    ):
        # Arrange
        notification2 = Mock()
        notification2.id = 2
        notification2.crypto_symbol = "ETH"
        notifications = [sample_notification, notification2]
        mock_notification_repository.list_by_account.return_value = notifications

        # Act
        result = notification_service.list_notifications_for_account(
            session=mock_session, account_id=1
        )

        # Assert
        assert len(result) == 2


class TestCheckAndProcessNotification:
    """Tests für check_and_process_notification"""

    def test_notification_triggered_above(
        self, notification_service, mock_notification_repository, mock_session, sample_notification
    ):
        # Arrange: Target 50.000, Preis jetzt 51.000
        sample_notification.direction = NotificationDirection.ABOVE
        sample_notification.target_price = 50000.00
        sample_notification.already_hit = False

        # Act
        result = notification_service.check_and_process_notification(
            session=mock_session, notif=sample_notification, current_price=51000.00
        )

        # Assert
        assert "Alert" in result.message
        assert result.current_price == 51000.00
        assert result.user_platform_id == "123456789"

        # Prüfen, ob Update im Repo gemacht wurde (already_hit = True)
        mock_notification_repository.update_already_hit.assert_called_once_with(
            session=mock_session, notification_id=sample_notification.id, already_hit=True
        )

    def test_notification_reset_when_price_drops_again(
        self, notification_service, mock_notification_repository, mock_session, sample_notification
    ):
        # Arrange: Notification wurde schon ausgelöst (already_hit = True)
        sample_notification.direction = NotificationDirection.ABOVE
        sample_notification.target_price = 50000.00
        sample_notification.already_hit = True

        # Preis jetzt wieder unter 50.000
        result = notification_service.check_and_process_notification(
            session=mock_session, notif=sample_notification, current_price=49000.00
        )

        # Assert: Es soll keine neue Nachricht gesendet werden, aber der Status resettet
        assert result.message == ""
        mock_notification_repository.update_already_hit.assert_called_once_with(
            session=mock_session, notification_id=sample_notification.id, already_hit=False
        )

    def test_notification_not_triggered(
        self, notification_service, mock_notification_repository, mock_session, sample_notification
    ):
        # Arrange
        sample_notification.direction = NotificationDirection.ABOVE
        sample_notification.target_price = 50000.00
        sample_notification.already_hit = False

        # Act: Preis unter Target
        result = notification_service.check_and_process_notification(
            session=mock_session, notif=sample_notification, current_price=49000.00
        )

        # Assert
        assert result.message == ""
        mock_notification_repository.update_already_hit.assert_not_called()


class TestCheckAllNotifications:
    """Tests für check_all_notifications"""

    @pytest.mark.asyncio
    @patch("app.services.notification_service.session_scope")
    async def test_check_all_notifications_returns_triggered(
        self,
        mock_session_scope,
        notification_service,
        mock_notification_repository,
        mock_crypto_api_service,
        sample_notification,
    ):
        # Arrange Session Scope Patch
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_scope.return_value = mock_context

        # Arrange Notifications
        sample_notification.direction = NotificationDirection.ABOVE
        sample_notification.target_price = 50000.00
        mock_notification_repository.list_by_platform.return_value = [sample_notification]

        # Arrange API Service (Fetch Ticker Prices statt get_price)
        mock_price = CryptoPrice(price=55000.00, error=False, only_usd=False)
        mock_crypto_api_service.fetch_ticker_prices.return_value = [("BTC", "USD", mock_price)]

        # Act
        results = await notification_service.check_all_notifications(PlatformType.DISCORD)

        # Assert
        assert len(results) == 1
        assert "Alert" in results[0].message

        # Prüfen, ob die API korrekt aufgerufen wurde
        mock_crypto_api_service.fetch_ticker_prices.assert_called_once_with(
            ticker_pairs={("BTC", "USD")}
        )
