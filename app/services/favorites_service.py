import logging
from sqlalchemy.orm import Session
from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.repository.favorites_repository import FavoritesRepository
from app.services.crypto_api_service import CryptoApiService
from app.models.schemas import Account


class FavoritesService:

    def __init__(
        self,
        favorite_repository: FavoritesRepository,
        cryptocurrency_repository: CryptocurrencyRepository,
        crypto_api_service: CryptoApiService,
    ):
        self._favorite_repository = favorite_repository
        self._cryptocurrency_repository = cryptocurrency_repository
        self._crypto_api_service = crypto_api_service

    def add_favorite(self, db_session: Session, account: Account, input_crypto: str) -> str:
        cryptocurrency = self._cryptocurrency_repository.find_by_name_or_symbol(
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
        cryptocurrency = self._cryptocurrency_repository.find_by_name_or_symbol(
            db_session=db_session, identifier=input_crypto
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
            vs_currency = account.selected_vs_currency.short_name.lower()
        message = "Your Favorite Cryptocurrencies:\n\n"
        for crypto_currency in favorites:
            try:
                message += await self._crypto_api_service.get_index_str(
                    crypto_currency_input=crypto_currency.full_name, vs_currency=vs_currency
                )
                message += "\n"
            except Exception as e:
                logging.error(f"Error fetching price for {crypto_currency.symbol}: {e}")
                message += f"• {crypto_currency.full_name} " f"({crypto_currency.symbol.upper()})\n"
                message += "   Price: Unavailable\n\n"
        return message

    def drop_favorites(self, account: Account) -> str:
        if not account.favorite_cryptos:
            return "ℹ️ You have no favorite cryptocurrencies to drop."
        self._favorite_repository.drop_favorites(account=account)
        return "✅ All favorite cryptocurrencies have been removed!"
