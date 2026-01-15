import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.general_service import GeneralService
from app.models import Coin

# Testen der Initialisierung / GeneralService-Klasse


@pytest.mark.asyncio
async def test_initialize_crypto_currencies_when_empty(mocker):

    # Setup
    mock_repo = MagicMock()
    mock_api = AsyncMock()

    # Szenario: Repository ist leer
    mock_repo.is_empty.return_value = True

    # Helper: Standardwerte für Felder, die für diesen Test nicht gebraucht werden,
    # die das Coin-Model aber zwingend verlangt.
    defaults = {
        "image": "http://test.com/image.png",
        "fully_diluted_valuation": 0,
        "total_volume": 1000,
        "high_24h": 0,
        "low_24h": 0,
        "price_change_24h": 0,
        "price_change_percentage_24h": 0,
        "market_cap_change_24h": 0,
        "market_cap_change_percentage_24h": 0,
        "circulating_supply": 0,
        "total_supply": 0,
        "max_supply": 0,
        "ath": 0,
        "ath_change_percentage": 0,
        "ath_date": "2022-01-01",
        "atl": 0,
        "atl_change_percentage": 0,
        "atl_date": "2020-01-01",
        "roi": None,
        "last_updated": "2023-01-01",
    }

    # API-Antwort mit 3 Coins, wobei "BTC" doppelt vorkommt
    # Test, ob Code das Duplikat rauswirft
    fake_coins = [
        Coin(
            id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            current_price=50000,
            market_cap=1,
            market_cap_rank=1,
            **defaults,
        ),
        Coin(
            id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            current_price=50000,
            market_cap=1,
            market_cap_rank=1,
            **defaults,
        ),
        Coin(
            id="ethereum",
            symbol="eth",
            name="Ethereum",
            current_price=3000,
            market_cap=2,
            market_cap_rank=2,
            **defaults,
        ),
    ]

    mock_api.list_top_crypto_currencies.return_value = fake_coins

    # Session Scope Mocking
    mock_session_scope = mocker.patch("app.services.general_service.session_scope")
    mock_session = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_session

    # Initialisieren des Services mit Mock
    service = GeneralService(mock_repo, mock_api)

    await service.initialize_crypto_currencies()

    # Assertions
    # Wurde die API gefragt?
    mock_api.list_top_crypto_currencies.assert_called_once_with(amount=100)
    # Wurde gespeichert?
    mock_repo.store_cryptocurrencies.assert_called_once()

    # Prüfen, was genau an store_cryptocurrencies übergeben wurde.
    stored_coins = mock_repo.store_cryptocurrencies.call_args[0][1]

    # Wir erwarten nur 2 Coins (BTC und ETH), das Duplikat muss weg sein.
    assert len(stored_coins) == 2
    assert stored_coins[0].symbol == "btc"
    assert stored_coins[1].symbol == "eth"


@pytest.mark.asyncio
async def test_initialize_does_nothing_when_repo_not_empty(mocker):
    # --- SETUP ---
    mock_repo = MagicMock()
    mock_api = MagicMock()

    # Repository ist nicht leer
    mock_repo.is_empty.return_value = False

    # Session Scope Mocking
    mocker.patch("app.services.general_service.session_scope")

    service = GeneralService(mock_repo, mock_api)

    # --- EXECUTION ---
    await service.initialize_crypto_currencies()

    # --- ASSERTION ---
    # API darf NICHT aufgerufen werden
    mock_api.list_top_crypto_currencies.assert_not_called()
    # Speichern darf nicht aufgerufen werden
    mock_repo.store_cryptocurrencies.assert_not_called()
