import pytest
from unittest.mock import AsyncMock
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.crypto_api_service import CryptoApiService
from app.repository.favorites_repository import FavoritesRepository
from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.models.schemas import PlatformType, Cryptocurrency, Account, VsCurrency
from app.services.favorites_service import FavoritesService


@pytest.mark.asyncio
async def test_full_favorite_lifecycle(db_session, mocker):
    # SETUP - Mock Variables
    mock_symbol = "BTC"
    mock_currency = "EUR"
    mock_price = 42000.00
    mock_price_message = f"{mock_symbol}-{mock_currency}: {mock_price:.2f} €"

    fav_repo = FavoritesRepository()
    crypto_repo = CryptocurrencyRepository()

    # API Mocken
    mock_http_client = AsyncMock()
    api_service = CryptoApiService(mock_http_client)
    crypto_currency_service = CryptoCurrencyService(crypto_repo, api_service)

    # Mock API methods
    mocker.patch.object(api_service, "get_index", new_callable=AsyncMock, return_value=999.99)
    mocker.patch.object(
        api_service, "get_prices", new_callable=AsyncMock, return_value=mock_price_message
    )

    favorites_service = FavoritesService(fav_repo, crypto_currency_service, api_service)

    # DATEN VORBEREITEN
    # Create VsCurrency first
    vs_currency = VsCurrency(symbol=mock_currency, name="Euro")
    db_session.add(vs_currency)
    db_session.flush()

    btc = Cryptocurrency(symbol=mock_symbol, name="Bitcoin")
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
    assert "Added Bitcoin (BTC) to favorites." in response_add

    # Prüfen in der DB
    db_session.refresh(account)
    assert account is not None
    assert len(account.favorite_cryptos) == 1

    # Auflisten
    response_list = await favorites_service.list_favorites(account)
    assert mock_symbol in response_list
    assert mock_price_message in response_list

    # Entfernen
    response_remove = favorites_service.remove_favorite(db_session, account, "bitcoin")
    assert "Removed Bitcoin (BTC) from favorites." in response_remove

    # Prüfen in der DB
    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 0

    # Leere Liste anzeigen
    response_empty = await favorites_service.list_favorites(account)
    assert "No favorites set yet." in response_empty
