import httpx
import json
from app.models import Coin


class CryptoApiService:
    BASE_URL = "https://api.coingecko.com/api/v3/coins"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def list_top_crypto_currencies(self, amount: int) -> list[Coin]:
        params: dict[str, str | int] = {
            "vs_currency": "eur",
            "order": "market_cap_desc",
            "per_page": amount,
        }
        url = f"{self.BASE_URL}/markets"
        response = await self.client.get(url, params=params)
        json_obj = json.loads(response.text)
        coins = [Coin(**coin_data) for coin_data in json_obj]
        return coins

    async def get_index(self, input: str) -> float:
        # TODO: Allow symbol as input aswell (must be done before)
        coin_id = input.lower().strip()
        params: dict[str, str] = {"vs_currency": "eur"}
        url = f"{self.BASE_URL}/{coin_id}"
        response = await self.client.get(url, params=params)
        json_obj = json.loads(response.text)
        result = json_obj.get("market_data", {}).get("current_price", {}).get("eur")
        return float(result)
