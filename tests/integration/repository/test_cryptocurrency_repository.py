from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.models import Cryptocurrency


def test_store_and_retrieve_cryptocurrencies(db_session, sample_coin):
    repo = CryptocurrencyRepository()

    sample_coin.name = "Bitcoin"
    sample_coin.symbol = "btc"

    # 1. Speichern
    repo.store_cryptocurrencies(db_session, [sample_coin])
    db_session.commit()

    # 2. Finden über Symbol (case insensitive Test: btc vs BTC)
    found_by_symbol = repo.find_by_name_or_symbol(db_session, "BTC")
    assert found_by_symbol is not None
    assert found_by_symbol.fullName == "Bitcoin"

    # 3. Finden über Name (case insensitive Test: bitcoin vs Bitcoin)
    found_by_name = repo.find_by_name_or_symbol(db_session, "bitcoin")
    assert found_by_name is not None
    assert found_by_name.symbol == "BTC"


def test_is_empty(db_session):
    repo = CryptocurrencyRepository()
    assert repo.is_empty(db_session) is True

    # Dummy Crypto einfügen
    crypto = Cryptocurrency(symbol="ETH", fullName="Ethereum")
    db_session.add(crypto)
    db_session.commit()

    assert repo.is_empty(db_session) is False
