import logging
from sqlalchemy.orm import Session
from app.models import Account, Cryptocurrency

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)


class FavoriteRepository:

    def add_favorite(self, session: Session, account: Account, crypto: Cryptocurrency):
        account.favorite_cryptos.append(crypto)

    def remove_favorite(self, session: Session, account: Account, crypto: Cryptocurrency):
        account.favorite_cryptos.remove(crypto)

    def drop_favorites(self, session: Session, account: Account) -> None:
        account.favorite_cryptos.clear()
