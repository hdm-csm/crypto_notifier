# Testen der Business-Logik der Crypto API Service
# Ziel: Testen, ob Daten von der API korrekt verarbeitet werden, ohne die echte API aufzurufen.
import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from app.services.crypto_api_service import CryptoApiService
from app.models.dtos import CoinMarketData

# Helper Dictionary für Pflichtfelder im Coin-Model
COIN_DEFAULTS = {
    "image": "http://test.com/image.png",
    "fully_diluted_valuation": 100000,
    "total_volume": 50000,
    "high_24h": 52000,
    "low_24h": 49000,
    "price_change_24h": 100,
    "price_change_percentage_24h": 0.5,
    "market_cap_change_24h": 1000,
    "market_cap_change_percentage_24h": 0.1,
    "circulating_supply": 18000000,
    "total_supply": 21000000,
    "max_supply": 21000000,
    "ath": 69000,
    "ath_change_percentage": -20,
    "ath_date": "2021-11-10",
    "atl": 67,
    "atl_change_percentage": 50000,
    "atl_date": "2013-07-06",
    "roi": None,
    "last_updated": "2023-01-01T00:00:00.000Z",
}


# Simuliert die "Markets"-API
@pytest.mark.asyncio
async def test_list_top_crypto_currencies_success():
    # --- SETUP ---
    # Mocken des HTTP Client
    mock_client = AsyncMock()

    # Simulieren der JSON-Antwort der API (ein Array von Coin-Objekten)
    api_response_data = [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 50000.0,
            "market_cap": 1000000,
            "market_cap_rank": 1,
            **COIN_DEFAULTS,
        },
        {
            "id": "ethereum",
            "symbol": "eth",
            "name": "Ethereum",
            "current_price": 3000.0,
            "market_cap": 500000,
            "market_cap_rank": 2,
            **COIN_DEFAULTS,
        },
    ]

    # Mock-Response Objekt, das eine .text Eigenschaft hat
    mock_response = MagicMock()
    mock_response.text = json.dumps(api_response_data)

    # Wenn client.get aufgerufen wird, gib unseren Mock-Response zurück
    mock_client.get.return_value = mock_response

    service = CryptoApiService(mock_client)

    # --- EXECUTION ---
    result = await service.get_top_crypto_currencies(amount=2)

    # --- ASSERTION ---
    # 1. Wurde die URL mit den richtigen Parametern aufgerufen?
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert "https://api.coingecko.com/api/v3/coins/markets" in args[0]
    assert kwargs["params"]["per_page"] == 2
    assert kwargs["params"]["vs_currency"] == "EUR"

    # 2. Wurden die Daten korrekt in Coin-Objekte umgewandelt?
    assert len(result) == 2
    assert isinstance(result[0], CoinMarketData)
    assert result[0].name == "Bitcoin"
    assert result[0].current_price == 50000.0
    assert result[1].symbol == "eth"
    assert result[1].id == "ethereum"


# Simuliert die get_index Methode mit yfinance
@pytest.mark.asyncio
async def test_get_index_success(mocker):
    # --- SETUP ---
    mock_client = AsyncMock()
    mock_ticker = MagicMock()
    mock_ticker.fast_info = {"last_price": 42500.50}
    mock_yf = mocker.patch("app.services.crypto_api_service.yf.Ticker", return_value=mock_ticker)
    service = CryptoApiService(mock_client)
    result = await service.get_index("btc", "EUR")
    mock_yf.assert_called_once_with("BTC-EUR")
    assert "BTC: 42500.50 €" in result
    assert isinstance(result, str)
