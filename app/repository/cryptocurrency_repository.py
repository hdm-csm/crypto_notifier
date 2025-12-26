import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Cryptocurrency, Coin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')


class CryptocurrencyRepository():

    def is_empty_wo_session(self, session: Session) -> bool:
        count = session.query(Cryptocurrency).count()
        return count == 0
    
    def is_empty(self, session: Session) -> bool:
        count = session.query(Cryptocurrency).count()
        return count == 0
    
    def exists(self, session: Session, identifier: str) -> bool:
        return session.query(Cryptocurrency).filter(
                (func.lower(Cryptocurrency.symbol) == func.lower(identifier)) |
                (func.lower(Cryptocurrency.fullName) == func.lower(identifier))
            ).first() is not None
    
    def find_by_name_or_symbol(self, session: Session, identifier: str) -> Cryptocurrency | None:
        return session.query(Cryptocurrency).filter(
            (func.lower(Cryptocurrency.symbol) == func.lower(identifier)) |
            (func.lower(Cryptocurrency.fullName) == func.lower(identifier))
            ).first()
    
    def get_all_cryptocurrencies(self, session: Session) -> list[Cryptocurrency]:
        return session.query(Cryptocurrency).all()
    
    def store_cryptocurrencies(self, session: Session, cryptocurrencies: list[Coin]):
        new_crypto_currencies = [
            Cryptocurrency(
                symbol=crypto.symbol.upper(),
                fullName=crypto.name
            )
            for crypto in cryptocurrencies
        ]
        session.add_all(new_crypto_currencies)
