import logging
from app.models.enums import PlatformType
from app.models.schemas import Account, VsCurrency
from app.repository.account_repository import AccountRepository
from app.repository.vs_currency_repository import VsCurrencyRepository
from app.utils.exceptions import AccountNotFoundOrCreatedException
from sqlalchemy.orm import Session


class AccountLookupService:
    def __init__(
        self,
        account_repository: AccountRepository,
        vs_currency_repository: VsCurrencyRepository,
    ):
        self._account_repository = account_repository
        self._vs_currency_repository = vs_currency_repository

    def find_or_create_account(
        self, db_session: Session, platform_type: PlatformType, platform_user_id: str
    ) -> Account:
        try:
            account = self._account_repository.find_by_platform_and_id(
                session=db_session, platform=platform_type, platform_user_id=platform_user_id
            )
            if account is None:
                euro: VsCurrency | None = self._vs_currency_repository.find_by_short_name(
                    db_session, "EUR"
                )
                selected_vs_currency_id: int = 0  # TODO: FIX
                if euro is not None:
                    selected_vs_currency_id = euro.id
                account = self._account_repository.create(
                    session=db_session,
                    platform=platform_type,
                    platform_user_id=platform_user_id,
                    selected_vs_currency_id=selected_vs_currency_id,
                )
            return account
        except Exception as e:
            logging.error(f"Error finding or creating account: {e}")
            raise AccountNotFoundOrCreatedException(
                original_message=str(e),
                custom_message=f"Could not find or create account for user ID {platform_user_id} on platform {platform_type.value}",
            ) from e
