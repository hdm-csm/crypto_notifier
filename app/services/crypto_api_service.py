import httpx
import json
from app.models.dtos import CoinMarketData, SimpleCoinPrice


class CryptoApiService:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def list_top_crypto_currencies(
        self, amount: int, vs_currency: str = "eur"
    ) -> list[CoinMarketData]:
        params: dict[str, str | int] = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": amount,
        }
        url = f"{self.BASE_URL}/coins/markets"
        response = await self.client.get(url, params=params)
        json_obj = json.loads(response.text)
        coins = [CoinMarketData(**coin_data) for coin_data in json_obj]
        return coins

    async def get_index(self, crypto_currency_input: str, vs_currency: str = "eur") -> float | None:
        crypto_currency_input = crypto_currency_input.lower().strip()
        currency_key = f"{vs_currency.lower()}"
        params: dict[str, str] = {
            "ids": crypto_currency_input,
            "vs_currencies": vs_currency.lower(),
            "include_24hr_change": "true",
            "include_last_updated_at": "true",
        }
        url = f"{self.BASE_URL}/simple/price"
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

    async def get_supported_vs_currencies(self) -> list[str]:
        url = f"{self.BASE_URL}/simple/supported_vs_currencies"
        response = await self.client.get(url)
        json_obj = json.loads(response.text)
        if not isinstance(json_obj, list):
            return []
        return [str(currency) for currency in json_obj]
