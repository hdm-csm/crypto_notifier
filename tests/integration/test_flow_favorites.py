import pytest
from unittest.mock import AsyncMock
from app.services.crypto_api_service import CryptoApiService
from app.repository.favorites_repository import FavoritesRepository
from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.models.schemas import PlatformType, Cryptocurrency, Account, VsCurrency
from app.services.favorites_service import FavoritesService


@pytest.mark.asyncio
async def test_full_favorite_lifecycle(db_session, mocker):
    # SETUP
    fav_repo = FavoritesRepository()
    crypto_repo = CryptocurrencyRepository()

    # API Mocken
    mock_http_client = AsyncMock()
    api_service = CryptoApiService(mock_http_client)

    # Mock get_index method
    mocker.patch.object(api_service, "get_index", new_callable=AsyncMock, return_value=999.99)

    favorites_service = FavoritesService(fav_repo, crypto_repo, api_service)

    # DATEN VORBEREITEN
    # Create VsCurrency first
    vs_currency = VsCurrency(short_name="EUR", full_name="Euro")
    db_session.add(vs_currency)
    db_session.flush()

    btc = Cryptocurrency(symbol="BTC", full_name="Bitcoin")
    db_session.add(btc)
    db_session.commit()

    user_id = "test_user_1"
    platform = PlatformType.DISCORD

    # Account erstellen
    account = Account(
        platform=platform, platform_user_id=user_id, selected_vs_currency_id=vs_currency.id
    )
    db_session.add(account)
    db_session.commit()

    # TEST FLOW

    # Favorit hinzufügen
    response_add = favorites_service.add_favorite(db_session, account, "bitcoin")
    assert "Saved bitcoin" in response_add

    # Prüfen in der DB
    db_session.refresh(account)
    assert account is not None
    assert len(account.favorite_cryptos) == 1

    # Auflisten
    response_list = await favorites_service.list_favorites(account)
    assert "Bitcoin" in response_list
    assert "999.99" in response_list

    # Entfernen
    response_remove = favorites_service.remove_favorite(db_session, account, "bitcoin")
    assert "Removed bitcoin" in response_remove

    # Prüfen in der DB
    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 0

    # Leere Liste anzeigen
    response_empty = await favorites_service.list_favorites(account)
    assert "no favorite cryptocurrencies" in response_empty
