import logging
from sqlalchemy.orm import Session
from app.models import Account, Cryptocurrency, PlatformType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
)


class FavoriteRepository:

    def add_favorite(self, session: Session, account: Account, crypto: Cryptocurrency):
        account.favorite_cryptos.append(crypto)

    def remove_favorite(self, session: Session, account: Account, crypto: Cryptocurrency):
        account.favorite_cryptos.remove(crypto)

    def get_favorites(
        self, session: Session, platform: PlatformType, platform_id: str
    ) -> list[Cryptocurrency]:
        account = (
            session.query(Account)
            .filter(Account.platform == platform, Account.platformId == str(platform_id))
            .first()
        )

        # Eagerly load to avoid lazy loading after session closes
        if account is not None:
            return list(account.favorite_cryptos)
        else:
            return []
