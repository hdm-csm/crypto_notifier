import logging
from app.models import PlatformType
from app.repository.account_repository import AccountRepository
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.repository.favorite_repository import FavoriteRepository
from app.db import session_scope
from app.services.crypto_api_service import CryptoApiService


class BotService:

    def __init__(
        self,
        account_repository: AccountRepository,
        favorite_repository: FavoriteRepository,
        cryptocurrency_repository: CryptocurrencyRepository,
        crypto_api_service: CryptoApiService,
    ):
        self._account_repository = account_repository
        self._favorite_repository = favorite_repository
        self._cryptocurrency_repository = cryptocurrency_repository
        self._crypto_api_service = crypto_api_service

    def add_favorite(self, platformType: PlatformType, user_id: str, input_crypto: str) -> str:
        try:
            with session_scope() as session:
                account = self._account_repository.find_by_platform_and_id(
                    session=session, platform=platformType, platform_id=user_id
                )
                if account is None:
                    account = self._account_repository.create(
                        session=session, platform=platformType, platformId=user_id
                    )

                if not account:
                    return f"⚠️ Could not find or create account for user ID {user_id}."

                cryptocurrency = self._cryptocurrency_repository.find_by_name_or_symbol(
                    session, input_crypto
                )

                if not cryptocurrency:
                    return (
                        f"⚠️ Cryptocurrency '{input_crypto}' not found. "
                        "Please check the name/symbol and try again."
                    )

                if cryptocurrency in account.favorite_cryptos:
                    return f"⚠️ {input_crypto} is already in your favorites."

                self._favorite_repository.add_favorite(
                    session=session, account=account, crypto=cryptocurrency
                )

                return f"✅ Saved {input_crypto} as your favorite cryptocurrency!"

        except Exception as e:
            logging.error(f"Error adding favorite: {e}")
            return "❌ An error occurred while saving your favorite. " "Please try again later."

    def remove_favorite(self, platformType: PlatformType, user_id: str, input_crypto: str) -> str:
        try:
            with session_scope() as session:
                account = self._account_repository.find_by_platform_and_id(
                    session=session, platform=platformType, platform_id=user_id
                )

                if account is None:
                    return f"⚠️ Account not found for user ID {user_id}."

                cryptocurrency = self._cryptocurrency_repository.find_by_name_or_symbol(
                    session, input_crypto
                )

                if not cryptocurrency:
                    return (
                        f"⚠️ Cryptocurrency '{input_crypto}' not found. "
                        "Please check the name/symbol and try again."
                    )

                if cryptocurrency not in account.favorite_cryptos:
                    return f"⚠️ {input_crypto} is not in your favorites."

                self._favorite_repository.remove_favorite(
                    session=session, account=account, crypto=cryptocurrency
                )

                return f"✅ Removed {input_crypto} from your favorites!"

        except Exception as e:
            logging.error(f"Error removing favorite: {e}")
            return "❌ An error occurred while removing your favorite. " "Please try again later."

    async def list_favorites(self, platformType: PlatformType, user_id: str) -> str:
        try:
            with session_scope() as session:
                account = self._account_repository.find_by_platform_and_id(
                    session=session, platform=platformType, platform_id=user_id
                )
                if account is None:
                    return "⚠️ Account not found."
                favorites = account.favorite_cryptos
                if not favorites or len(favorites) == 0:
                    return "ℹ️ You have no favorite cryptocurrencies yet."
                message = "Your Favorite Cryptocurrencies:\n\n"
                for crypto_currency in favorites:
                    try:
                        price: float | None = await self._crypto_api_service.get_index(
                            crypto_currency.fullName
                        )
                        if price is not None:
                            message += (
                                f"• {crypto_currency.fullName} "
                                f"({crypto_currency.symbol.upper()})\n"
                            )
                            message += f"   Price: {price:.2f} €\n"
                        else:
                            message += (
                                f"• {crypto_currency.fullName} "
                                f"({crypto_currency.symbol.upper()})\n"
                            )
                            message += "   Price: Unavailable\n\n"
                    except Exception as e:
                        logging.error(f"Error fetching price for {crypto_currency.symbol}: {e}")
                        message += (
                            f"• {crypto_currency.fullName} " f"({crypto_currency.symbol.upper()})\n"
                        )
                        message += "   Price: Unavailable\n\n"
                return message
        except Exception as e:
            logging.error(f"Error listing favorites: {e}")
            return "❌ An error occurred while listing your favorites. " "Please try again later."

    def drop_favorites(self, platformType: PlatformType, user_id: str) -> str:
        try:
            with session_scope() as session:
                account = self._account_repository.find_by_platform_and_id(
                    session=session, platform=platformType, platform_id=user_id
                )
                if account is None:
                    return "⚠️ Account not found."
                if not account.favorite_cryptos:
                    return "ℹ️ You have no favorite cryptocurrencies to drop."
                self._favorite_repository.drop_favorites(session=session, account=account)
                return "✅ All favorite cryptocurrencies have been removed!"
        except Exception as e:
            logging.error(f"Error dropping favorites: {e}")
            return "❌ An error occurred while dropping your favorites. " "Please try again later."
