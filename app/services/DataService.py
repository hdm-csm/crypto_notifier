import httpx
import json
from app.models.Coin import Coin


class DataService:

    @property
    def api_url1(self):
        return "https://api.coingecko.com/api/v3/coins/markets"

    def list_top_10_crypto_currencies(self) -> list[Coin]:
        params = {
                'vs_currency': 'usd',
                'order': 'market_cap',
                'per_page': 10,
                'page': 1
        }
        r = httpx.get(self.api_url1, params=params)
        json_obj = json.loads(r.text)
        coins = [
            Coin(**coin_data)
            for coin_data in json_obj
        ]
        return coins

