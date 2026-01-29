import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.general_service import GeneralService
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.services.crypto_api_service import CryptoApiService
from app.models import Coin


@pytest.mark.asyncio
async def test_startup_initialization_fills_db(db_session, mocker):
    # SETUP
    crypto_repo = CryptocurrencyRepository()

    # API Mocken
    mock_http_client = AsyncMock()
    api_service = CryptoApiService(mock_http_client)

    # Fake Antwort der API: 2 Coins
    fake_coins = [
        Coin(
            id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            current_price=50000,
            market_cap=1,
            market_cap_rank=1,
            image="",
            fully_diluted_valuation=0,
            total_volume=0,
            high_24h=0,
            low_24h=0,
            price_change_24h=0,
            price_change_percentage_24h=0,
            market_cap_change_24h=0,
            market_cap_change_percentage_24h=0,
            circulating_supply=0,
            total_supply=0,
            max_supply=0,
            ath=0,
            ath_change_percentage=0,
            ath_date="",
            atl=0,
            atl_change_percentage=0,
            atl_date="",
            roi=None,
            last_updated="",
        ),
        Coin(
            id="ethereum",
            symbol="eth",
            name="Ethereum",
            current_price=3000,
            market_cap=2,
            market_cap_rank=2,
            image="",
            fully_diluted_valuation=0,
            total_volume=0,
            high_24h=0,
            low_24h=0,
            price_change_24h=0,
            price_change_percentage_24h=0,
            market_cap_change_24h=0,
            market_cap_change_percentage_24h=0,
            circulating_supply=0,
            total_supply=0,
            max_supply=0,
            ath=0,
            ath_change_percentage=0,
            ath_date="",
            atl=0,
            atl_change_percentage=0,
            atl_date="",
            roi=None,
            last_updated="",
        ),
    ]

    api_service.list_top_crypto_currencies = AsyncMock(return_value=fake_coins)

    # Session scope patchen
    mock_scope = MagicMock()
    mock_scope.__enter__.return_value = db_session
    mock_scope.__exit__.return_value = None

    mocker.patch("app.services.general_service.session_scope", return_value=mock_scope)

    general_service = GeneralService(crypto_repo, api_service)

    # EXECUTION
    # Datenbank am Anfang leer
    assert crypto_repo.is_empty(db_session) is True

    # Initialisierung ausführen
    await general_service.initialize_crypto_currencies()
    db_session.commit()

    # ASSERTION
    # 2 Coins sollten jetzt in der DB sein
    assert crypto_repo.is_empty(db_session) is False

    stored_btc = crypto_repo.find_by_name_or_symbol(db_session, "BTC")
    assert stored_btc is not None
    assert stored_btc.full_name == "Bitcoin"
