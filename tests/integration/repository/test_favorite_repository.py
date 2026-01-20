from app.repository.favorite_repository import FavoriteRepository
from app.models import Account, Cryptocurrency, PlatformType
from datetime import datetime


def test_add_and_remove_favorite(db_session):
    repo = FavoriteRepository()

    # User und Crypto anlegen
    account = Account(platform=PlatformType.Discord, platformId="user1", created_at=datetime.now())
    crypto = Cryptocurrency(symbol="DOGE", fullName="Dogecoin")

    db_session.add(account)
    db_session.add(crypto)
    db_session.commit()

    # Hinzufügen als Favorit
    repo.add_favorite(db_session, account, crypto)
    db_session.commit()

    # Prüfungen
    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 1
    assert account.favorite_cryptos[0].symbol == "DOGE"

    # Entfernen aus Favoriten
    repo.remove_favorite(db_session, account, crypto)
    db_session.commit()

    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 0


def test_drop_favorites(db_session):
    repo = FavoriteRepository()

    # User mit 2 Favoriten
    account = Account(platform=PlatformType.Telegram, platformId="user2", created_at=datetime.now())
    c1 = Cryptocurrency(symbol="A", fullName="A-Coin")
    c2 = Cryptocurrency(symbol="B", fullName="B-Coin")

    db_session.add_all([account, c1, c2])
    db_session.commit()

    # Manuell hinzufügen
    account.favorite_cryptos.append(c1)
    account.favorite_cryptos.append(c2)
    db_session.commit()

    assert len(account.favorite_cryptos) == 2

    # alle Favoriten entfernen
    repo.drop_favorites(db_session, account)
    db_session.commit()

    db_session.refresh(account)
    assert len(account.favorite_cryptos) == 0
