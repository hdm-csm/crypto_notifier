import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.schemas import Cryptocurrency
from app.models.dtos import CoinMarketData

logger = logging.getLogger(__name__)


class CryptocurrencyRepository:

    def is_empty(self, session: Session) -> bool:
        return session.query(Cryptocurrency).count() == 0

    def exists(self, session: Session, identifier: str) -> bool:
        return (
            session.query(Cryptocurrency)
            .filter(
                (func.lower(Cryptocurrency.symbol) == func.lower(identifier))
                | (func.lower(Cryptocurrency.name) == func.lower(identifier))
            )
            .first()
            is not None
        )

    def find_by_name_or_symbol(self, db_session: Session, identifier: str) -> Cryptocurrency | None:
        return (
            db_session.query(Cryptocurrency)
            .filter(
                (func.lower(Cryptocurrency.symbol) == func.lower(identifier))
                | (func.lower(Cryptocurrency.name) == func.lower(identifier))
            )
            .first()
        )

    def get_all(self, session: Session) -> list[Cryptocurrency]:
        return session.query(Cryptocurrency).all()

    def store_all(self, session: Session, coins: list[CoinMarketData]):
        new_cryptos = [Cryptocurrency(symbol=coin.symbol.upper(), name=coin.name) for coin in coins]
        session.add_all(new_cryptos)
