import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.bot_service import BotService
from app.services.crypto_api_service import CryptoApiService
from app.repository.account_repository import AccountRepository
from app.repository.favorite_repository import FavoriteRepository
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.models import PlatformType, Cryptocurrency


@pytest.mark.asyncio
async def test_full_favorite_lifecycle(db_session, mocker):
    # SETUP
    account_repo = AccountRepository()
    fav_repo = FavoriteRepository()
    crypto_repo = CryptocurrencyRepository()

    # API Mocken
    mock_http_client = AsyncMock()
    api_service = CryptoApiService(mock_http_client)
    api_service.get_index = AsyncMock(return_value=999.99)

    # session_scope patchen

    mock_scope = MagicMock()

    mock_scope.__enter__.return_value = db_session
    mock_scope.__exit__.return_value = None

    mocker.patch("app.services.bot_service.session_scope", return_value=mock_scope)

    # Service mit echten Repos und Fake-API erstellen
    bot_service = BotService(account_repo, fav_repo, crypto_repo, api_service)

    # DATEN VORBEREITEN
    btc = Cryptocurrency(symbol="BTC", fullName="Bitcoin")
    db_session.add(btc)
    db_session.commit()

    user_id = "test_user_1"
    platform = PlatformType.Discord

    # TEST FLOW

    # Favorit hinzufügen
    response_add = bot_service.add_favorite(platform, user_id, "bitcoin")
    assert "Saved bitcoin" in response_add

    # Prüfen in der DB
    account = account_repo.find_by_platform_and_id(db_session, platform, user_id)
    assert account is not None
    assert len(account.favorite_cryptos) == 1

    # Auflisten
    response_list = await bot_service.list_favorites(platform, user_id)
    assert "Bitcoin" in response_list
    assert "999.99 €" in response_list

    # Entfernen
    response_remove = bot_service.remove_favorite(platform, user_id, "bitcoin")
    assert "Removed bitcoin" in response_remove

    # Prüfen in der DB
    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 0

    # Leere Liste anzeigen
    response_empty = await bot_service.list_favorites(platform, user_id)
    assert "no favorite cryptocurrencies" in response_empty
