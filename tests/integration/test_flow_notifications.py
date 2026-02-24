import pytest
import contextlib
from unittest.mock import AsyncMock

from app.models.dtos import CryptoPrice
from app.models.enums import PlatformType, NotificationDirection
from app.models.schemas import Account, VsCurrency
from app.repository.notification_repository import NotificationRepository
from app.services.crypto_api_service import CryptoApiService
from app.services.notification_service import NotificationService


@pytest.mark.asyncio
async def test_full_notification_lifecycle(db_session, mocker):

    # SETUP & MOCKS
    @contextlib.contextmanager
    def fake_session_scope():
        yield db_session
        db_session.commit()

    mocker.patch("app.services.notification_service.session_scope", fake_session_scope)

    notif_repo = NotificationRepository()

    # API Mocken
    mock_http_client = AsyncMock()
    api_service = CryptoApiService(mock_http_client)

    mock_fetch = mocker.patch.object(
        api_service,
        "fetch_ticker_prices",
        new_callable=AsyncMock,
    )

    notification_service = NotificationService(notif_repo, api_service)

    # Daten vorbereiten
    # Währung anlegen
    vs_currency = VsCurrency(symbol="USD", name="US Dollar")
    db_session.add(vs_currency)
    db_session.flush()

    # User Account anlegen
    user_id = "discord_user_999"
    platform = PlatformType.DISCORD
    account = Account(
        platform=platform, platform_user_id=user_id, selected_vs_currency_id=vs_currency.id
    )
    db_session.add(account)
    db_session.commit()

    # Account ID für den Service speichern
    acc_id = account.id

    # Test Flow: Notification Lifecycle

    # SCHRITT A: Notification hinzufügen (Ziel: BTC > 50000 USD)
    new_notif = notification_service.add_notification(
        session=db_session,
        account_id=acc_id,
        crypto_symbol="BTC",
        vs_symbol="USD",
        direction=NotificationDirection.ABOVE,
        target_price=50000.0,
        already_hit=False,
    )
    db_session.commit()

    assert new_notif.id is not None
    assert new_notif.crypto_symbol == "BTC"

    # Liste abrufen und prüfen
    notif_list = notification_service.list_notifications_for_account(db_session, acc_id)
    assert len(notif_list) == 1
    assert notif_list[0].target_price == 50000.0

    # SCHRITT B: Preis steigt ÜBER das Ziel (Auslösen der Notification)
    mock_fetch.return_value = [("BTC", "USD", CryptoPrice(price=51000.0))]

    results = await notification_service.check_all_notifications(PlatformType.DISCORD)

    assert len(results) == 1
    assert "Alert" in results[0].message
    assert "51000.0" in results[0].message

    # DB muss 'already_hit' True sein
    db_session.refresh(notif_list[0])
    assert notif_list[0].already_hit is True

    # SCHRITT C: Preis steigt weiter, nicht nochmal auslösen
    mock_fetch.return_value = [("BTC", "USD", CryptoPrice(price=52000.0))]

    results_second_check = await notification_service.check_all_notifications(PlatformType.DISCORD)

    assert len(results_second_check) == 0

    # SCHRITT D: Preis fällt wieder UNTER das Ziel (Reset)
    mock_fetch.return_value = [("BTC", "USD", CryptoPrice(price=49000.0))]

    results_reset = await notification_service.check_all_notifications(PlatformType.DISCORD)

    # Leere Liste
    assert len(results_reset) == 0

    # Prüfung ob reset geklappt hat
    db_session.refresh(notif_list[0])
    assert notif_list[0].already_hit is False

    # SCHRITT E: Notification entfernen
    is_removed = notification_service.remove_notification(db_session, new_notif.id)
    db_session.commit()

    assert is_removed is True

    # Prüfen, ob sie wirklich weg ist
    empty_list = notification_service.list_notifications_for_account(db_session, acc_id)
    assert len(empty_list) == 0
