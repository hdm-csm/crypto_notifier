from sqlalchemy.orm import Session
from app.models.dtos import CryptoPrice
from app.models.typealiases import CryptoSymbolStr, VsCurrencySymbolStr
from app.repository.favorites_repository import FavoritesRepository
from app.services.crypto_api_service import CryptoApiService
from app.models.schemas import Account
from app.services.crypto_currency_service import CryptoCurrencyService
from app.utils.functions import get_currency_display


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
            return f"❌ '{input_crypto}' not found."
        if cryptocurrency in account.favorite_cryptos:
            return f"⚠️ {input_crypto} is already in your favorites."
        self._favorite_repository.add_favorite(account=account, crypto=cryptocurrency)
        return f"✅ Added {cryptocurrency.name} ({cryptocurrency.symbol}) to favorites."

    def remove_favorite(self, db_session: Session, account: Account, input_crypto: str) -> str:
        cryptocurrency = self._crypto_currency_service.find_by_name_or_symbol(
            db_session=db_session, input=input_crypto
        )
        if not cryptocurrency:
            return f"❌ '{input_crypto}' not found."
        if cryptocurrency not in account.favorite_cryptos:
            return f"⚠️ {input_crypto} is not in your favorites."
        self._favorite_repository.remove_favorite(account=account, crypto=cryptocurrency)
        return f"✅ Removed {cryptocurrency.name} ({cryptocurrency.symbol}) from favorites."

    async def list_favorites(self, account: Account) -> str:
        favorites = account.favorite_cryptos
        if not favorites or len(favorites) == 0:
            return "ℹ️ No favorites set yet."
        vs_currency = "EUR"
        if account and account.selected_vs_currency:
            vs_currency = account.selected_vs_currency.symbol.lower()
        crypto_symbols = [crypto.symbol for crypto in favorites]
        ticker_pairs = {(crypto, vs_currency) for crypto in crypto_symbols}
        favorite_prices = await self._crypto_api_service.fetch_ticker_prices(
            ticker_pairs=ticker_pairs
        )
        message = "⭐ Favorites\n\n"
        message += self.format_ticker_prices(favorite_prices)
        return message

    def drop_favorites(self, account: Account) -> str:
        if not account.favorite_cryptos:
            return "ℹ️ No favorites to remove."
        self._favorite_repository.drop_favorites(account=account)
        return "✅ All favorites removed."

    @staticmethod
    def format_ticker_prices(
        ticker_results: list[tuple[CryptoSymbolStr, VsCurrencySymbolStr, CryptoPrice]],
    ) -> str:
        """Formats a list of ticker results into a readable multi-line string."""
        if not ticker_results:
            return "ℹ️ No price data available for favorites."
        lines = []
        for crypto, vs, price_info in ticker_results:
            c, v = crypto.upper(), vs.upper()
            if price_info.error:
                lines.append(f"• {c}/{v}: ❌ Unavailable")
                continue
            p = price_info.price
            if p == 0.0:
                price_str = "0.00"
            elif p >= 1.0:
                price_str = f"{p:,.2f}"
            else:
                price_str = f"{p:,.6f}".rstrip("0").rstrip(".")
            vs_display = get_currency_display(v)
            vs_prefix = f"{vs_display} " if len(vs_display) > 1 else vs_display
            if price_info.only_usd:
                usd_prefix = get_currency_display("USD")
                lines.append(f"• {c}/{v}: {usd_prefix}{price_str} (Fallback)")
            elif price_info.self_converted:
                lines.append(f"• {c}/{v}: ≈ {vs_prefix}{price_str} (Self-Converted)")
            else:
                lines.append(f"• {c}/{v}: {vs_prefix}{price_str}")

        return "\n".join(lines)
