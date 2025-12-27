from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from sqlalchemy.orm import Session
from app.services.crypto_api_service import CryptoApiService
from app.db import session_scope

class GeneralService:
    def __init__(
        self,
        cryptocurrency_repository: CryptocurrencyRepository,
        crypto_api_service: CryptoApiService
    ):
        self._cryptocurrency_repository = cryptocurrency_repository
        self._crypto_api_service = crypto_api_service

    async def initialize_crypto_currencies(self):
        with session_scope() as session:
            if self._cryptocurrency_repository.is_empty(session):
                coins = await self._crypto_api_service.list_top_crypto_currencies(amount=100)
                
                # Filter out duplicates by symbol
                seen_symbols = set()
                unique_coins = []
                for coin in coins:
                    if coin.symbol not in seen_symbols:
                        seen_symbols.add(coin.symbol)
                        unique_coins.append(coin)

                self._cryptocurrency_repository.store_cryptocurrencies(session, unique_coins)
