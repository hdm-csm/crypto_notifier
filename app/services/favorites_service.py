from sqlalchemy.orm import Session
from app.repository.favorites_repository import FavoritesRepository
from app.services.crypto_api_service import CryptoApiService
from app.models.schemas import Account
from app.services.crypto_currency_service import CryptoCurrencyService


class FavoritesService:

    def __init__(
        self,
        favorite_repository: FavoritesRepository,
        crypto_currency_service: CryptoCurrencyService,
        crypto_api_service: CryptoApiService,
    ):
        self._favorite_repository = favorite_repository
        self._crypto_currency_service = crypto_currency_service
        self._crypto_api_service = crypto_api_service

    def add_favorite(self, db_session: Session, account: Account, input_crypto: str) -> str:
        cryptocurrency = self._crypto_currency_service.find_by_name_or_symbol(
            db_session, input_crypto
        )
        if not cryptocurrency:
            return (
                f"⚠️ Cryptocurrency '{input_crypto}' not found. "
                "Please check the name/symbol and try again."
            )
        if cryptocurrency in account.favorite_cryptos:
            return f"⚠️ {input_crypto} is already in your favorites."
        self._favorite_repository.add_favorite(account=account, crypto=cryptocurrency)
        return f"✅ Saved {input_crypto} as your favorite cryptocurrency!"

    def remove_favorite(self, db_session: Session, account: Account, input_crypto: str) -> str:
        cryptocurrency = self._crypto_currency_service.find_by_name_or_symbol(
            db_session=db_session, input=input_crypto
        )
        if not cryptocurrency:
            return (
                f"⚠️ Cryptocurrency '{input_crypto}' not found. "
                "Please check the name/symbol and try again."
            )
        if cryptocurrency not in account.favorite_cryptos:
            return f"⚠️ {input_crypto} is not in your favorites."
        self._favorite_repository.remove_favorite(account=account, crypto=cryptocurrency)
        return f"✅ Removed {input_crypto} from your favorites!"

    async def list_favorites(self, account: Account) -> str:
        favorites = account.favorite_cryptos
        if not favorites or len(favorites) == 0:
            return "ℹ️ You have no favorite cryptocurrencies yet."
        vs_currency = "eur"
        if account and account.selected_vs_currency:
            vs_currency = account.selected_vs_currency.symbol.lower()

        crypto_symbols = [crypto.symbol for crypto in favorites]
        # prices_str = await self._crypto_api_service.get_indexes(
        #     crypto_symbols=crypto_symbols, vs_currency_symbol=vs_currency
        # )
        prices_str = await self._crypto_api_service.get_prices(
            tickers=[f"{symbol}-{vs_currency}" for symbol in crypto_symbols]
        )

        message = "Your Favorite Cryptocurrencies:\n\n"
        message += prices_str
        return message

    def drop_favorites(self, account: Account) -> str:
        if not account.favorite_cryptos:
            return "ℹ️ You have no favorite cryptocurrencies to drop."
        self._favorite_repository.drop_favorites(account=account)
        return "✅ All favorite cryptocurrencies have been removed!"
