import logging
from app.models.schemas import Account, Cryptocurrency

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)


class FavoriteRepository:

    def add_favorite(self, account: Account, crypto: Cryptocurrency):
        account.favorite_cryptos.append(crypto)

    def remove_favorite(self, account: Account, crypto: Cryptocurrency):
        account.favorite_cryptos.remove(crypto)

    def drop_favorites(self, account: Account) -> None:
        account.favorite_cryptos.clear()
