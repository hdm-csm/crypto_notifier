from app.db import session_scope
from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.services.crypto_api_service import CryptoApiService


class CryptoCurrencyService:
    def __init__(
        self,
        crypto_currency_repository: CryptocurrencyRepository,
        crypto_api_service: CryptoApiService,
    ):
        self._crypto_currency_repository = crypto_currency_repository
        self._crypto_api_service = crypto_api_service

    async def init_crypto_currencies(self):
        with session_scope() as session:
            if self._crypto_currency_repository.is_empty(session):
                coins = await self._crypto_api_service.list_top_crypto_currencies(amount=100)

                # Filter out duplicates by symbol
                seen_symbols = set()
                unique_coins = []
                for coin in coins:
                    if coin.symbol not in seen_symbols:
                        seen_symbols.add(coin.symbol)
                        unique_coins.append(coin)

                self._crypto_currency_repository.store_all(session, unique_coins)
