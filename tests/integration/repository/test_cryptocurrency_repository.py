import pytest
from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.models.schemas import Cryptocurrency
from app.models.dtos import CoinMarketData


@pytest.fixture
def mock_bitcoin():
    return CoinMarketData(
        id="bitcoin",
        symbol="btc",
        name="Bitcoin",
        image="url",
        current_price=50000.0,
        market_cap=1000000,
        market_cap_rank=1,
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
    )


@pytest.fixture
def mock_ethereum():
    return CoinMarketData(
        id="ethereum",
        symbol="eth",
        name="Ethereum",
        image="url",
        current_price=3000.0,
        market_cap=360000,
        market_cap_rank=2,
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
    )


@pytest.fixture
def stored_bitcoin(db_session, mock_bitcoin):
    repo = CryptocurrencyRepository()
    repo.store_all(db_session, [mock_bitcoin])
    db_session.commit()
    return mock_bitcoin


@pytest.fixture
def stored_bitcoin_and_ethereum(db_session, mock_bitcoin, mock_ethereum):
    repo = CryptocurrencyRepository()
    repo.store_all(db_session, [mock_bitcoin, mock_ethereum])
    db_session.commit()
    return [mock_bitcoin, mock_ethereum]


def test_store_and_retrieve_cryptocurrencies(db_session, stored_bitcoin):
    repo = CryptocurrencyRepository()
    # Verify the fixture set it up correctly
    assert stored_bitcoin.name == "Bitcoin"

    # 2. Finden über Symbol (case insensitive Test: btc vs BTC)
    found_by_symbol = repo.find_by_name_or_symbol(db_session, "BTC")
    assert found_by_symbol is not None
    assert found_by_symbol.name == "Bitcoin"

    # 3. Finden über Name (case insensitive Test: bitcoin vs Bitcoin)
    found_by_name = repo.find_by_name_or_symbol(db_session, "bitcoin")
    assert found_by_name is not None
    assert found_by_name.symbol == "BTC"


def test_is_empty(db_session):
    repo = CryptocurrencyRepository()
    assert repo.is_empty(db_session) is True

    # Dummy Crypto einfügen
    crypto = Cryptocurrency(symbol="ETH", name="Ethereum")
    db_session.add(crypto)
    db_session.commit()

    assert repo.is_empty(db_session) is False


def test_exists(db_session, stored_bitcoin):
    repo = CryptocurrencyRepository()

    # 2. Check ob Symbol existiert (case insensitive)
    assert repo.exists(db_session, "btc") is True
    assert repo.exists(db_session, "BTC") is True

    # 3. Check ob Name existiert (case insensitive)
    assert repo.exists(db_session, "bitcoin") is True
    assert repo.exists(db_session, "Bitcoin") is True

    # 4. Check ob nicht existiertes Symbol nicht gefunden wird
    assert repo.exists(db_session, "XYZ") is False


def test_get_all_cryptocurrencies(db_session, stored_bitcoin_and_ethereum):
    repo = CryptocurrencyRepository()

    # 3. Hole alle und prüfe die Anzahl
    all_cryptos = repo.get_all(db_session)
    assert len(all_cryptos) == 2

    # 4. Prüfe die Symbole
    symbols = {crypto.symbol for crypto in all_cryptos}
    assert "BTC" in symbols
    assert "ETH" in symbols
