# Testen der Business-Logik der Crypto API Service
# Ziel: Testen, ob Daten von der API korrekt verarbeitet werden, ohne die echte API aufzurufen.
import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from app.services.crypto_api_service import CryptoApiService
from app.models import Coin

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
    result = await service.list_top_crypto_currencies(amount=2)

    # --- ASSERTION ---
    # 1. Wurde die URL mit den richtigen Parametern aufgerufen?
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert "https://api.coingecko.com/api/v3/coins/markets" in args[0]
    assert kwargs["params"]["per_page"] == 2
    assert kwargs["params"]["vs_currency"] == "eur"

    # 2. Wurden die Daten korrekt in Coin-Objekte umgewandelt?
    assert len(result) == 2
    assert isinstance(result[0], Coin)
    assert result[0].name == "Bitcoin"
    assert result[0].current_price == 50000.0
    assert result[1].symbol == "eth"
    assert result[1].id == "ethereum"


# Simuliert die Detail-API
@pytest.mark.asyncio
async def test_get_index_success():
    # --- SETUP ---
    mock_client = AsyncMock()

    api_response_data = {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "market_data": {"current_price": {"eur": 45000.50, "usd": 50000.00}},
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(api_response_data)
    mock_client.get.return_value = mock_response

    service = CryptoApiService(mock_client)

    # --- EXECUTION ---
    price = await service.get_index(" Bitcoin ")

    # --- ASSERTION ---
    # Prüfen ob die URL korrekt gebaut wurde (lowercase und stripped)
    mock_client.get.assert_called_once()
    args, _ = mock_client.get.call_args
    assert "https://api.coingecko.com/api/v3/coins/bitcoin" in args[0]

    # Prüfen ob der Preis korrekt extrahiert wurde
    assert price == 45000.50
    assert isinstance(price, float)


# Simuliert den Fall, dass ein Coin nicht existiert
@pytest.mark.asyncio
async def test_get_index_not_found_or_invalid_structure():
    # --- SETUP ---
    mock_client = AsyncMock()

    # Szenario 1: API liefert leeres JSON oder Fehler (Coin nicht gefunden)
    api_response_data = {"error": "Could not find coin with the given id"}

    mock_response = MagicMock()
    mock_response.text = json.dumps(api_response_data)
    mock_client.get.return_value = mock_response

    service = CryptoApiService(mock_client)

    # --- EXECUTION ---
    result = await service.get_index("unknown-coin")

    # --- ASSERTION ---
    # Der Service sollte None zurückgeben, wenn er den Pfad market_data -> current_price -> eur nicht findet
    assert result is None
