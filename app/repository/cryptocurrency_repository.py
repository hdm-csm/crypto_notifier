import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Cryptocurrency, Coin
from app.services.session_manager import SessionManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')


class CryptocurrencyRepository(SessionManager):

    def is_empty_wo_session(db: Session) -> bool:
        count = db.query(Cryptocurrency).count()
        return count == 0
    
    def is_empty(self) -> bool:
        with self.get_session() as db:
            count = db.query(Cryptocurrency).count()
            return count == 0
    
    def exists(self, identifier: str) -> bool:
        """Check if cryptocurrency exists by symbol or full name (case-insensitive)."""
        with self.get_session() as db:
            return db.query(Cryptocurrency).filter(
                (func.lower(Cryptocurrency.symbol) == func.lower(identifier)) |
                (func.lower(Cryptocurrency.fullName) == func.lower(identifier))
            ).first() is not None
    
    def find_by_name_or_symbol(self, identifier: str) -> Cryptocurrency | None:
        """Find cryptocurrency by symbol or full name (case-insensitive)."""
        with self.get_session() as db:
            return db.query(Cryptocurrency).filter(
                (func.lower(Cryptocurrency.symbol) == func.lower(identifier)) |
                (func.lower(Cryptocurrency.fullName) == func.lower(identifier))
            ).first()
    
    def get_all_cryptocurrencies(self) -> list[Cryptocurrency]:
        # returns detached ORM object --> accessing props tries to access session...
        with self.get_session() as db:
            return db.query(Cryptocurrency).all()
    
    def get_all_cryptocurrency_names(self) -> list[str]:
        with self.get_session() as db:
            return [crypto.fullName for crypto in db.query(Cryptocurrency).all()]
    
    def store_cryptocurrencies(self, cryptocurrencies: list[Coin]) -> bool:
        """Store cryptocurrencies in the database."""
        with self.get_session() as db:
            for crypto in cryptocurrencies:
                new_crypto = Cryptocurrency(
                    symbol=crypto.symbol.upper(),
                    fullName=crypto.name
                )
                db.add(new_crypto)
            
            logging.info(f"Stored {len(cryptocurrencies)} cryptocurrencies")
            return True
