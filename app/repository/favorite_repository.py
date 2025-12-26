import logging
from sqlalchemy.orm import Session
from app.models import Account, Cryptocurrency, PlatformType
from app.services.session_manager import SessionManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')


class FavoriteRepository(SessionManager):
    
    def add_favorite(self, account: Account, crypto: Cryptocurrency) -> bool:
        with self.get_session() as db:
            account.favorite_cryptos.append(crypto)
            return True
    
    def remove_favorite(self, platform: PlatformType, platform_id: str, symbol: str) -> bool:
        with self.get_session() as db:
            account = db.query(Account).filter(
                Account.platform == platform,
                Account.platformId == str(platform_id)
            ).first()
            
            if not account:
                logging.error(f"Account not found for {platform_id}")
                return False
            
            crypto = db.query(Cryptocurrency).filter(
                Cryptocurrency.symbol == symbol.upper()
            ).first()
            
            if not crypto:
                logging.error(f"Cryptocurrency {symbol} not found")
                return False
            
            if crypto not in account.favorite_cryptos:
                logging.info(f"{symbol} not in favorites for {platform_id}")
                return False
            
            account.favorite_cryptos.remove(crypto)
            logging.info(f"Removed {symbol} from favorites for {platform_id}")
            return True
    
    def get_favorites(self, platform: PlatformType, platform_id: str) -> list[Cryptocurrency]:
        with self.get_session() as db:
            account = db.query(Account).filter(
                Account.platform == platform,
                Account.platformId == str(platform_id)
            ).first()
            
            if not account:
                logging.info(f"Account not found for {platform_id}")
                return []
            
            # Eagerly load to avoid lazy loading after session closes
            return list(account.favorite_cryptos)
