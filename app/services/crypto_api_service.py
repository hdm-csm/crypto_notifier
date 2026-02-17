import httpx
import json
from app.models.dtos import CoinMarketData, SimpleCoinPrice
from app.utils.functions import get_currency_display
from config.config import Config

COINGECKO_API_KEY = Config.COINGECKO_API_KEY


# if pair not supported + its weekend -> write (forex change from friday)


class CryptoApiService:
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"  # Rate Limit = 10K requests/month
    BINANCE_BASE_URL = "https://api.binance.com/api/v3"  # Unlimited requests

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def list_top_crypto_currencies(
        self, amount: int, vs_currency: str = "eur"
    ) -> list[CoinMarketData]:
        params: dict[str, str | int] = {
            "x_cg_demo_api_key": COINGECKO_API_KEY,
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": amount,
        }
        url = f"{self.COINGECKO_BASE_URL}/coins/markets"
        response = await self.client.get(url, params=params)
        json_obj = json.loads(response.text)
        # list[CoinMarketData] =
        coins = [CoinMarketData(**coin_data) for coin_data in json_obj]
        return coins

    async def list_top_crypto_currencies_str(self, amount: int, vs_currency: str = "eur") -> str:
        coins = await self.list_top_crypto_currencies(amount, vs_currency)
        currency_display = get_currency_display(vs_currency)
        message = "Top 10 Cryptocurrencies by Market Cap:\n\n"
        for coin in coins:
            message += f"{coin.market_cap_rank}. {coin.name} ({coin.symbol.upper()})\n"
            message += f"   Price: {coin.current_price:.2f} {currency_display}\n"
            message += f"   Market Cap: {coin.market_cap:,} {currency_display}\n"
            message += f"   Index ID: {coin.id}\n\n"
        return message

    async def get_index(self, crypto_currency_input: str, vs_currency: str = "eur") -> float | None:
        crypto_currency_input = crypto_currency_input.lower().strip()
        currency_key = f"{vs_currency.lower()}"
        params: dict[str, str] = {
            "x_cg_demo_api_key": COINGECKO_API_KEY,
            "ids": crypto_currency_input,
            "vs_currencies": vs_currency.lower(),
            "include_24hr_change": "true",
            "include_last_updated_at": "true",
        }
        url = f"{self.COINGECKO_BASE_URL}/simple/price"
        try:
            response = await self.client.get(url, params=params)
            json_obj = json.loads(response.text)
            if crypto_currency_input not in json_obj:
                return None
            coin_data = json_obj[crypto_currency_input]
            simple_price = SimpleCoinPrice(
                price=coin_data.get(currency_key),
                market_cap=coin_data.get(f"{currency_key}_market_cap"),
                volume_24h=coin_data.get(f"{currency_key}_24h_vol"),
                change_24h=coin_data.get(f"{currency_key}_24h_change"),
                last_updated_at=coin_data.get("last_updated_at"),
            )
            if simple_price.price is not None:
                return float(simple_price.price)
            return None
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            return None

    async def get_index_str(self, crypto_currency_input: str, vs_currency: str = "eur") -> str:
        result = await self.get_index(crypto_currency_input, vs_currency)
        if result is None:
            return f'Could not find price for "{crypto_currency_input}". \nPlease enter correct id.'
        currency_display = get_currency_display(vs_currency)
        return f"{crypto_currency_input.capitalize()}: {result:.2f} {currency_display}"

    async def get_coingecko_supported_vs_currencies(self) -> list[str]:
        url = f"{self.COINGECKO_BASE_URL}/simple/supported_vs_currencies"
        response = await self.client.get(url)
        json_obj = json.loads(response.text)
        if not isinstance(json_obj, list):
            return []
        return [str(currency) for currency in json_obj]

    async def get_notification_index(
        self, base_asset: str, quote_asset: str = "USDT"
    ) -> float | None:
        url = (
            f"{self.BINANCE_BASE_URL}/ticker/price?symbol={base_asset.upper()}{quote_asset.upper()}"
        )
        try:
            response = await self.client.get(url)
            json_obj = json.loads(response.text)
            price_str = json_obj.get("price")
            if price_str is not None:
                return float(price_str)
            return None
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            return None
