import pytest
from unittest.mock import AsyncMock
import contextlib
from app.models.enums import PlatformType
from app.models.schemas import VsCurrency, Cryptocurrency
from app.models.dtos import CryptoPrice

# Repositories
from app.repository.account_repository import AccountRepository
from app.repository.vs_currency_repository import VsCurrencyRepository
from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.repository.favorites_repository import FavoritesRepository
from app.repository.notification_repository import NotificationRepository

# Services
from app.services.account_lookup_service import AccountLookupService
from app.services.vs_currency_service import VsCurrencyService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.crypto_api_service import CryptoApiService
from app.services.favorites_service import FavoritesService
from app.services.notification_service import NotificationService
from app.utils.exceptions import InvalidNotificationArguments


@pytest.fixture
def setup_services(db_session, mocker):
    """
    Baut die komplette Service-Architektur auf und faked die API sowie die Datenbank-Session.
    Gibt ein Dictionary mit allen benötigten Services zurück.
    """
    # 1. Repositories
    account_repo = AccountRepository()
    vs_currency_repo = VsCurrencyRepository()
    crypto_repo = CryptocurrencyRepository()
    fav_repo = FavoritesRepository()
    notif_repo = NotificationRepository()

    # 2. API Mock
    mock_http_client = AsyncMock()
    api_service = CryptoApiService(mock_http_client)

    # 3. Services
    account_lookup = AccountLookupService(account_repo, vs_currency_repo)
    vs_currency_service = VsCurrencyService(vs_currency_repo, account_lookup, api_service)
    crypto_currency_service = CryptoCurrencyService(crypto_repo, api_service)
    favorites_service = FavoritesService(fav_repo, crypto_currency_service, api_service)
    notification_service = NotificationService(notif_repo, api_service)

    # 4. Globalen Session-Scope patchen (damit alle Services dieselbe Test-DB nutzen)
    @contextlib.contextmanager
    def fake_session_scope():
        yield db_session
        db_session.commit()

    mocker.patch(
        "app.services.account_lookup_service.session_scope", fake_session_scope, create=True
    )
    mocker.patch("app.services.vs_currency_service.session_scope", fake_session_scope, create=True)
    mocker.patch(
        "app.services.crypto_currency_service.session_scope", fake_session_scope, create=True
    )
    mocker.patch("app.services.favorites_service.session_scope", fake_session_scope, create=True)
    mocker.patch("app.services.notification_service.session_scope", fake_session_scope, create=True)

    # 5. Grunddaten in die DB schreiben
    eur = VsCurrency(symbol="EUR", name="Euro")
    usd = VsCurrency(symbol="USD", name="US Dollar")
    btc = Cryptocurrency(symbol="BTC", name="Bitcoin")
    eth = Cryptocurrency(symbol="ETH", name="Ethereum")

    db_session.add_all([eur, usd, btc, eth])
    db_session.commit()

    return {
        "account_lookup": account_lookup,
        "vs_currency": vs_currency_service,
        "favorites": favorites_service,
        "notifications": notification_service,
        "api": api_service,
    }


@pytest.mark.asyncio
async def test_flow_onboarding_and_settings(db_session, setup_services):
    """
    Journey 1: Ein neuer User schreibt den Bot an und ändert seine Standardwährung.
    """
    services = setup_services
    platform = PlatformType.DISCORD
    user_id = "new_user_123"

    # 1. User interagiert das erste Mal -> Account wird erstellt (Fallback auf EUR)
    account = services["account_lookup"].find_or_create_account(db_session, platform, user_id)
    assert account is not None
    assert account.platform_user_id == user_id

    assert account.selected_vs_currency.symbol == "EUR"

    # 2. User ruft `/set_vs usd` auf
    response = services["vs_currency"].set_vs_currency(db_session, account, "usd")
    db_session.commit()

    assert "✅" in response
    assert "USD" in response

    # 3. DB prüfen auf Persistenz
    db_session.refresh(account)
    assert account.selected_vs_currency.symbol == "USD"


@pytest.mark.asyncio
async def test_flow_favorites_management(db_session, setup_services, mocker):
    """
    Journey 2: User fügt einen Favoriten hinzu, versucht einen ungültigen hinzuzufügen
    und ruft die Liste ab.
    """
    services = setup_services
    platform = PlatformType.TELEGRAM
    user_id = "crypto_fan_99"

    # API Mock für die Preisabfrage der Favoritenliste
    mocker.patch.object(
        services["api"],
        "fetch_ticker_prices",
        return_value=[
            (
                "BTC",
                "eur",
                CryptoPrice(price=60000.0, error=False, only_usd=False, self_converted=False),
            )
        ],
    )

    # 1. Account holen
    account = services["account_lookup"].find_or_create_account(db_session, platform, user_id)

    # 2. User fügt existierenden Coin hinzu (`/add_fav btc`)
    add_valid = services["favorites"].add_favorite(db_session, account, "btc")
    db_session.commit()
    assert "✅" in add_valid

    # 3. User versucht Quatsch hinzuzufügen (`/add_fav fantasiecoin`)
    add_invalid = services["favorites"].add_favorite(db_session, account, "fantasiecoin")
    assert "❌" in add_invalid
    assert "not found" in add_invalid

    # 4. User ruft Favoritenliste ab (`/list_fav`)
    db_session.refresh(account)
    list_response = await services["favorites"].list_favorites(account)

    assert "⭐ Favorites" in list_response
    assert "BTC" in list_response
    assert "60,000" in list_response


@pytest.mark.asyncio
async def test_flow_invalid_notification_creation(db_session, setup_services):
    """
    Journey 3: User versucht eine Benachrichtigung mit falschen Parametern zu erstellen.
    Prüft das Error-Handling.
    """
    services = setup_services
    platform = PlatformType.DISCORD
    user_id = "alert_user_01"

    # 1. Account holen
    account = services["account_lookup"].find_or_create_account(db_session, platform, user_id)

    # 2. User tippt z.B. `/add_notif btc usd mitte 50000`
    with pytest.raises(InvalidNotificationArguments) as exc:
        services["notifications"].validate_and_parse_notification_args(
            crypto_symbol="btc", vs_symbol="usd", direction="mitte", price=50000.0  # Fehler
        )

    # 3. Sicherstellen, dass die Fehlermeldung den Usage-Hint für den Discord-User enthält
    assert "Direction must be 'above' or 'below'" in str(exc.value)

    # 4. Sicherstellen, dass keine Notification in die DB geschrieben wurde
    notifs = services["notifications"].list_notifications_for_account(db_session, account.id)
    assert len(notifs) == 0
