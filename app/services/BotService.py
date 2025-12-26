from pytest import Session

from app.services.session_manager import SessionManager
from app.repository.cryptocurrency_repository import CryptocurrencyRepository


class BotService():

    def __init__(
            self,
            session_manager: SessionManager,
            cryptocurrency_repository: CryptocurrencyRepository,
    ):
        self._session_manager = session_manager
        self._cryptocurrency_repository = cryptocurrency_repository

        
    def is_crypto_empty(self) -> bool:
        with self._session_manager.get_session() as db:
            return self._cryptocurrency_repository.is_empty_wo_session(db)
        