import logging
from pytest import Session
from app.repository.account_repository import AccountRepository
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.repository.favorite_repository import FavoriteRepository
from sqlalchemy.orm import sessionmaker
from app.services.crypto_api_service import CryptoApiService

class GeneralService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        cryptocurrency_repository: CryptocurrencyRepository,
        crypto_api_service: CryptoApiService
    ):
        self._session_factory = session_factory
        self._cryptocurrency_repository = cryptocurrency_repository
        self._crypto_api_service = crypto_api_service

    async def initialize_crypto_currencies(self):
        with self._session_factory as session, session.begin():
            if self._cryptocurrency_repository.is_empty(session):
                crypto_currencies = await self._crypto_api_service.list_top_crypto_currencies(amount=100)
                self._cryptocurrency_repository.store_cryptocurrencies(session, crypto_currencies)
