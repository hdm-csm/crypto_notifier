import pytest
import contextlib
from unittest.mock import AsyncMock

from app.models.enums import PlatformType
from app.models.schemas import VsCurrency, Cryptocurrency
from app.repository.account_repository import AccountRepository
from app.repository.vs_currency_repository import VsCurrencyRepository
from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.repository.favorites_repository import FavoritesRepository
from app.repository.notification_repository import NotificationRepository
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.crypto_api_service import CryptoApiService
from app.services.favorites_service import FavoritesService
from app.services.notification_service import NotificationService


@pytest.fixture
def setup_services(db_session, mocker):
    """Baut die Test-Architektur auf."""
    account_repo = AccountRepository()
    vs_currency_repo = VsCurrencyRepository()
    crypto_repo = CryptocurrencyRepository()
    fav_repo = FavoritesRepository()
    notif_repo = NotificationRepository()

    mock_http_client = AsyncMock()
    api_service = CryptoApiService(mock_http_client)

    account_lookup = AccountLookupService(account_repo, vs_currency_repo)
    crypto_currency_service = CryptoCurrencyService(crypto_repo, api_service)
    favorites_service = FavoritesService(fav_repo, crypto_currency_service, api_service)
    notification_service = NotificationService(notif_repo, api_service)

    @contextlib.contextmanager
    def fake_session_scope():
        yield db_session
        db_session.commit()

    mocker.patch(
        "app.services.account_lookup_service.session_scope", fake_session_scope, create=True
    )
    mocker.patch("app.services.favorites_service.session_scope", fake_session_scope, create=True)
    mocker.patch("app.services.notification_service.session_scope", fake_session_scope, create=True)

    # Basisdaten anlegen
    eur = VsCurrency(symbol="EUR", name="Euro")
    btc = Cryptocurrency(symbol="BTC", name="Bitcoin")
    eth = Cryptocurrency(symbol="ETH", name="Ethereum")
    db_session.add_all([eur, btc, eth])
    db_session.commit()

    # Test-Account anlegen
    account = account_lookup.find_or_create_account(db_session, PlatformType.DISCORD, "edge_user_1")
    db_session.commit()

    return {
        "account": account,
        "crypto_service": crypto_currency_service,
        "favorites": favorites_service,
        "notifications": notification_service,
        "api": api_service,
    }


@pytest.mark.asyncio
async def test_flow_read_operations_prevent_unnecessary_api_calls(db_session, setup_services):
    """
    Lesende Operationen (Info/Chart)
    Prüft, ob bei unbekannten Coins die DB greift und die API nicht aufgreufen wird.
    """
    services = setup_services
    account = services["account"]

    services["api"].fetch_ticker_prices = AsyncMock()

    # Aktion 1: User versucht Favorit hinzuzufügen, den es nicht gibt
    invalid_response = services["favorites"].add_favorite(db_session, account, "fantasiecoin")

    # Assert
    assert "❌" in invalid_response
    assert "not found" in invalid_response
    services["api"].fetch_ticker_prices.assert_not_called()


@pytest.mark.asyncio
async def test_flow_bulk_operations_partial_success(db_session, setup_services):
    """
    Test 2: Massenverarbeitung
    Simuliert `/add_favs btc eth fantasiecoin` und `/drop_favs`.
    """
    services = setup_services
    account = services["account"]

    # Aktion 1: User übergibt Liste mit validen und invaliden Coins
    inputs = ["btc", "fantasiecoin", "eth"]
    responses = []

    for coin in inputs:
        resp = services["favorites"].add_favorite(db_session, account, coin)
        responses.append(resp)

    db_session.commit()

    # Assert 1: Richtiges Feedback für jeden Coin
    assert "✅" in responses[0]
    assert "❌" in responses[1]
    assert "✅" in responses[2]

    # Assert 2: Nur 2 Coins sind in der DB gelandet
    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 2

    # Act 2: Drop All
    drop_response = services["favorites"].drop_favorites(account)
    db_session.commit()

    # Assert 3: DB ist komplett leer
    assert "✅" in drop_response
    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 0


@pytest.mark.asyncio
async def test_flow_chaos_monkey_api_timeout(db_session, setup_services, mocker):
    """
    Test 3: API Ausfall (Chaos Monkey)
    Prüft, dass ein API-Timeout korrekt nach oben gemeldet wird,
    da der Batch-Abruf kritisch für den Prozess ist.
    """
    services = setup_services

    # 1. Notification anlegen
    from app.models.enums import NotificationDirection

    services["notifications"].add_notification(
        session=db_session,
        account_id=services["account"].id,
        crypto_symbol="BTC",
        vs_symbol="USD",
        direction=NotificationDirection.ABOVE,
        target_price=50000.0,
    )
    db_session.commit()

    # 2. Arrange: API wirft einen Timeout-Fehler beim Batch-Abruf
    services["api"].fetch_ticker_prices = AsyncMock(side_effect=TimeoutError("API is down!"))

    # 3. Act & Assert: Prüfe, dass der Timeout korrekt propagiert wird
    with pytest.raises(TimeoutError) as exc:
        await services["notifications"].check_all_notifications(PlatformType.DISCORD)

    assert "API is down!" in str(exc.value)

    # Verifiziere, dass die DB-Session noch intakt ist
    assert db_session.is_active is True
