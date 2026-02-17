from app.db import session_scope
from app.models.schemas import Cryptocurrency
from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.services.crypto_api_service import CryptoApiService
from sqlalchemy.orm import Session


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
                coins = await self._crypto_api_service.get_top_crypto_currencies(amount=1000)

                # Filter out duplicates by symbol
                seen_symbols = set()
                unique_coins = []
                for coin in coins:
                    if coin.symbol not in seen_symbols:
                        seen_symbols.add(coin.symbol)
                        unique_coins.append(coin)

                self._crypto_currency_repository.store_all(session, unique_coins)

    def find_by_name_or_symbol(self, db_session: Session, input: str) -> Cryptocurrency | None:
        return self._crypto_currency_repository.find_by_name_or_symbol(db_session, input)

    def get_all(self, db_session: Session) -> str:
        crypto_currencies: list[Cryptocurrency] = self._crypto_currency_repository.get_all(
            db_session
        )
        if not crypto_currencies:
            return "No cryptocurrencies found."

        title = "List of all supported cryptocurrencies:"
        header = "Name (Symbol)"
        separator = "-" * len(header)
        rows = [title, "", header, separator]
        rows.extend([f"{coin.name} ({coin.symbol})" for coin in crypto_currencies])
        return "\n".join(rows)
