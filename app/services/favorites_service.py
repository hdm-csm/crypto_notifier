import logging
from sqlalchemy.orm import Session
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.repository.favorite_repository import FavoriteRepository
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.models.schemas import Account


class FavoritesService:

    def __init__(
        self,
        favorite_repository: FavoriteRepository,
        cryptocurrency_repository: CryptocurrencyRepository,
        crypto_api_service: CryptoApiService,
        account_lookup_service: AccountLookupService,
    ):
        self._favorite_repository = favorite_repository
        self._cryptocurrency_repository = cryptocurrency_repository
        self._crypto_api_service = crypto_api_service
        self._account_lookup_service = account_lookup_service

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
        message = "Your Favorite Cryptocurrencies:\n\n"
        for crypto_currency in favorites:
            try:
                price: float | None = await self._crypto_api_service.get_index(
                    crypto_currency.full_name
                )
                if price is not None:
                    message += (
                        f"• {crypto_currency.full_name} " f"({crypto_currency.symbol.upper()})\n"
                    )
                    message += f"   Price: {price:.2f} €\n"
                else:
                    message += (
                        f"• {crypto_currency.full_name} " f"({crypto_currency.symbol.upper()})\n"
                    )
                    message += "   Price: Unavailable\n\n"
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
