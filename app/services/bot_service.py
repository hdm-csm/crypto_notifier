import logging
from pytest import Session
from app.models import PlatformType
from app.repository.account_repository import AccountRepository
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.repository.favorite_repository import FavoriteRepository
from sqlalchemy.orm import sessionmaker


class BotService():

    def __init__(
            self,
            session_factory: sessionmaker[Session],
            account_repository: AccountRepository,
            favorite_repository: FavoriteRepository,
            cryptocurrency_repository: CryptocurrencyRepository,
    ):
        self._session_factory = session_factory
        self._account_repository = account_repository
        self._favorite_repository = favorite_repository
        self._cryptocurrency_repository = cryptocurrency_repository

        
    def is_crypto_empty(self) -> bool:
        with self._session_factory.get_session() as db:
            return self._cryptocurrency_repository.is_empty_wo_session(db)
        
    def add_favorite(self, platformType: PlatformType, user_id: str, input_crypto: str) -> str:
        try:
            with self._session_factory as session, session.begin(): # begin() handles the commit, rollback, and close automatically
                account = self._account_repository.find_by_platform_and_id(
                    session=session,
                    platform=platformType,
                    platform_id=user_id
                )
                if account is None:
                    account = self._account_repository.create(
                        session=session,
                        platform=platformType,
                        platformId=user_id
                    )
                
                if not account:
                    return f"⚠️ Could not find or create account for user ID {user_id}."

                cryptocurrency = self._cryptocurrency_repository.find_by_name_or_symbol(session, input_crypto)

                if not cryptocurrency:
                    return f"⚠️ Cryptocurrency '{input_crypto}' not found. Please check the name/symbol and try again."

                if cryptocurrency in account.favorite_cryptos:
                    return f"⚠️ {input_crypto} is already in your favorites."

                self._favorite_repository.add_favorite(
                    session=session,
                    account=account,
                    crypto=cryptocurrency
                )
                
                return f"✅ Saved {input_crypto} as your favorite cryptocurrency!"
                
        except Exception as e:
            logging.error(f"Error adding favorite: {e}")
            return "❌ An error occurred while saving your favorite. Please try again later."
        