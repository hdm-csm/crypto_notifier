import pytest
from app.repository.favorites_repository import FavoritesRepository
from app.models.schemas import Account, Cryptocurrency, VsCurrency
from app.models.enums import PlatformType


@pytest.fixture
def mock_vs_currency_usd(db_session):
    vs_currency = VsCurrency(short_name="USD", full_name="US Dollar")
    db_session.add(vs_currency)
    db_session.commit()
    return vs_currency


@pytest.fixture
def mock_vs_currency_eur(db_session):
    vs_currency = VsCurrency(short_name="EUR", full_name="Euro")
    db_session.add(vs_currency)
    db_session.commit()
    return vs_currency


@pytest.fixture
def mock_account_discord(db_session, mock_vs_currency_usd):
    account = Account(
        platform=PlatformType.DISCORD,
        platform_user_id="user1",
        selected_vs_currency_id=mock_vs_currency_usd.id,
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def mock_account_telegram(db_session, mock_vs_currency_eur):
    account = Account(
        platform=PlatformType.TELEGRAM,
        platform_user_id="user2",
        selected_vs_currency_id=mock_vs_currency_eur.id,
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def mock_crypto_doge(db_session):
    crypto = Cryptocurrency(symbol="DOGE", full_name="Dogecoin")
    db_session.add(crypto)
    db_session.commit()
    return crypto


@pytest.fixture
def mock_crypto_a(db_session):
    crypto = Cryptocurrency(symbol="A", full_name="A-Coin")
    db_session.add(crypto)
    db_session.commit()
    return crypto


@pytest.fixture
def mock_crypto_b(db_session):
    crypto = Cryptocurrency(symbol="B", full_name="B-Coin")
    db_session.add(crypto)
    db_session.commit()
    return crypto


def test_add_and_remove_favorite(db_session, mock_account_discord, mock_crypto_doge):
    repo = FavoritesRepository()

    account = mock_account_discord
    crypto = mock_crypto_doge

    # Hinzufügen als Favorit
    repo.add_favorite(account, crypto)
    db_session.commit()

    # Prüfungen
    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 1
    assert account.favorite_cryptos[0].symbol == "DOGE"

    # Entfernen aus Favoriten
    repo.remove_favorite(account, crypto)
    db_session.commit()

    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 0


def test_drop_favorites(db_session, mock_account_discord, mock_crypto_a, mock_crypto_b):
    repo = FavoritesRepository()
    account = mock_account_discord

    # Hinzufügen als Favorit
    repo.add_favorite(account, mock_crypto_a)
    repo.add_favorite(account, mock_crypto_b)
    db_session.commit()
    assert len(account.favorite_cryptos) == 2

    # alle Favoriten entfernen
    repo.drop_favorites(account)
    db_session.commit()

    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 0
