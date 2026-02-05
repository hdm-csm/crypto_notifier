import logging
from app.models.enums import PlatformType
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.repository.favorite_repository import FavoriteRepository
from app.db import session_scope
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.models.schemas import Account
from app.utils.exceptions import AccountNotFoundOrCreatedException


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

    def add_favorite(
        self, platform_type: PlatformType, platform_user_id: str, input_crypto: str
    ) -> str:
        try:
            with session_scope() as session:
                account: Account = self._account_lookup_service.find_or_create_account(
                    session=session, platform_type=platform_type, platform_user_id=platform_user_id
                )

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

        except AccountNotFoundOrCreatedException as e:
            logging.exception(str(e))
            return "⚠️ Account not found for user."
        except Exception as e:
            logging.error(f"Error adding favorite: {e}")
            return "❌ An error occurred while saving your favorite. " "Please try again later."

    def remove_favorite(
        self, platform_type: PlatformType, platform_user_id: str, input_crypto: str
    ) -> str:
        try:
            with session_scope() as session:
                account: Account = self._account_lookup_service.find_or_create_account(
                    session=session, platform_type=platform_type, platform_user_id=platform_user_id
                )

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

        except AccountNotFoundOrCreatedException as e:
            logging.exception(str(e))
            return "⚠️ Account not found for user."
        except Exception as e:
            logging.error(f"Error removing favorite: {e}")
            return "❌ An error occurred while removing your favorite. " "Please try again later."

    async def list_favorites(self, platform_type: PlatformType, platform_user_id: str) -> str:
        try:
            with session_scope() as session:
                account: Account = self._account_lookup_service.find_or_create_account(
                    session=session, platform_type=platform_type, platform_user_id=platform_user_id
                )
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
                                f"• {crypto_currency.full_name} "
                                f"({crypto_currency.symbol.upper()})\n"
                            )
                            message += f"   Price: {price:.2f} €\n"
                        else:
                            message += (
                                f"• {crypto_currency.full_name} "
                                f"({crypto_currency.symbol.upper()})\n"
                            )
                            message += "   Price: Unavailable\n\n"
                    except Exception as e:
                        logging.error(f"Error fetching price for {crypto_currency.symbol}: {e}")
                        message += (
                            f"• {crypto_currency.full_name} "
                            f"({crypto_currency.symbol.upper()})\n"
                        )
                        message += "   Price: Unavailable\n\n"
                return message
        except AccountNotFoundOrCreatedException as e:
            logging.exception(str(e))
            return "⚠️ Account not found for user."
        except Exception as e:
            logging.error(f"Error listing favorites: {e}")
            return "❌ An error occurred while listing your favorites. " "Please try again later."

    def drop_favorites(self, platform_type: PlatformType, platform_user_id: str) -> str:
        try:
            with session_scope() as session:
                account: Account = self._account_lookup_service.find_or_create_account(
                    session=session, platform_type=platform_type, platform_user_id=platform_user_id
                )
                if not account.favorite_cryptos:
                    return "ℹ️ You have no favorite cryptocurrencies to drop."
                self._favorite_repository.drop_favorites(session=session, account=account)
                return "✅ All favorite cryptocurrencies have been removed!"
        except AccountNotFoundOrCreatedException as e:
            logging.exception(str(e))
            return "⚠️ Account not found for user."
        except Exception as e:
            logging.error(f"Error dropping favorites: {e}")
            return "❌ An error occurred while dropping your favorites. " "Please try again later."
