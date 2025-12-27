import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Account, PlatformType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
)


class AccountRepository:

    def exists(self, session: Session, platform: PlatformType, platform_id: str) -> bool:
        return bool(
            session.query(Account)
            .filter(Account.platform == platform, Account.platformId == str(platform_id))
            .exists()
            .scalar()
        )

    def find_by_platform_and_id(
        self, session: Session, platform: PlatformType, platform_id: str
    ) -> Account | None:
        return (
            session.query(Account)
            .filter(Account.platform == platform, Account.platformId == str(platform_id))
            .first()
        )

    def create(self, session: Session, platform: PlatformType, platformId: str) -> Account:
        new_account = Account(
            platform=platform, platformId=str(platformId), created_at=datetime.now()
        )
        session.add(new_account)
        session.commit()
        session.refresh(new_account)
        logging.info(f"Created new {platform.value} account for {platformId}")
        return new_account
