import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Account, PlatformType
from app.services.session_manager import SessionManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')


class AccountRepository(SessionManager):

    def exists(self, platform: PlatformType, platform_id: str) -> bool:
        with self.get_session() as db:
            return db.query(Account).filter(
                Account.platform == platform,
                Account.platformId == str(platform_id)
            ).exists().scalar()

    def find_by_platform_and_id(self, platform: PlatformType, platform_id: str) -> Account | None:
        with self.get_session() as db:
            return db.query(Account).filter(
                Account.platform == platform,
                Account.platformId == str(platform_id)
            ).first()
        
    def create(self, platform: PlatformType, platformId: str) -> Account:
        with self.get_session() as db:
            new_account = Account(
                platform=platform,
                platformId=str(platformId),
                created_at=datetime.now()
            )
            db.add(new_account)
            db.commit()
            db.refresh(new_account)
            logging.info(f"Created new {platform.value} account for {platformId}")
            return new_account
    
    
