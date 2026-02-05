import logging
from datetime import datetime

# from unittest import result
from sqlalchemy.orm import Session
from app.models.schemas import Account, PlatformType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)


class AccountRepository:

    def exists(self, session: Session, platform: PlatformType, platform_user_id: str) -> bool:
        result: Account | None = (
            session.query(Account)
            .filter(Account.platform == platform, Account.platform_user_id == str(platform_user_id))
            .first()
        )
        return result is not None

    def find_by_platform_and_id(
        self, session: Session, platform: PlatformType, platform_user_id: str
    ) -> Account | None:
        return (
            session.query(Account)
            .filter(Account.platform == platform, Account.platform_user_id == str(platform_user_id))
            .first()
        )

    def create(
        self,
        session: Session,
        platform: PlatformType,
        platform_user_id: str,
        preferred_fiat_currency_id: int,
    ) -> Account:
        new_account = Account(
            platform=platform,
            platform_user_id=platform_user_id,
            preferred_fiat_currency_id=preferred_fiat_currency_id,
            created_at=datetime.now(),
        )
        session.add(new_account)
        session.flush()
        session.refresh(new_account)
        logging.info(f"Created new {platform.value} account for {platform_user_id}")
        return new_account

    def set_fiat_currency(
        self,
        session: Session,
        account: Account,
        fiat_currency_id: int,
    ) -> Account:
        account.selected_fiat_currency_id = fiat_currency_id
        session.flush()
        # session.refresh(account) not needed here
        logging.info(
            f"Set preferred fiat currency to ID {fiat_currency_id} for "
            f"{account.platform.value} account {account.platform_user_id}"
        )
        return account
