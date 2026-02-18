from typing import List, Dict, Optional
import httpx
import json

from yahooquery import Screener
from app.models.dtos import CoinMarketData, TickerResult
from app.models.schemas import Cryptocurrency
from app.utils.functions import get_currency_display
from config.config import Config
import yfinance as yf
import pandas as pd

COINGECKO_API_KEY = Config.COINGECKO_API_KEY


# if pair not supported + its weekend -> write (forex change from friday)


class CryptoApiService:
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"  # Rate Limit = 10K requests/month
    BINANCE_BASE_URL = "https://api.binance.com/api/v3"  # Unlimited requests

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_top_crypto_currencies(
        self, amount: int, vs_currency: str = "eur"
    ) -> list[CoinMarketData]:
        amount = max(1, min(amount, 100))  # Ensure amount is between 1 and 100
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

    async def get_top_crypto_currencies_str(self, amount: int, vs_currency: str = "eur") -> str:
        coins = await self.get_top_crypto_currencies(amount, vs_currency)
        currency_display = get_currency_display(vs_currency)
        message = "Top 10 Cryptocurrencies by Market Cap:\n\n"
        for coin in coins:
            message += f"{coin.market_cap_rank}. {coin.name} ({coin.symbol.upper()})\n"
            message += f"   Price: {coin.current_price:.2f} {currency_display}\n"
            message += f"   Market Cap: {coin.market_cap:,} {currency_display}\n"
            message += f"   Index ID: {coin.id}\n\n"
        return message

    # async def get_index(self, crypto_currency_input: str, vs_currency: str = "eur") -> float | None:
    #     crypto_currency_input = crypto_currency_input.lower().strip()
    #     currency_key = f"{vs_currency.lower()}"
    #     params: dict[str, str] = {
    #         "x_cg_demo_api_key": COINGECKO_API_KEY,
    #         "ids": crypto_currency_input,
    #         "vs_currencies": vs_currency.lower(),
    #         "include_24hr_change": "true",
    #         "include_last_updated_at": "true",
    #     }
    #     url = f"{self.COINGECKO_BASE_URL}/simple/price"
    #     try:
    #         response = await self.client.get(url, params=params)
    #         json_obj = json.loads(response.text)
    #         if crypto_currency_input not in json_obj:
    #             return None
    #         coin_data = json_obj[crypto_currency_input]
    #         simple_price = SimpleCoinPrice(
    #             price=coin_data.get(currency_key),
    #             market_cap=coin_data.get(f"{currency_key}_market_cap"),
    #             volume_24h=coin_data.get(f"{currency_key}_24h_vol"),
    #             change_24h=coin_data.get(f"{currency_key}_24h_change"),
    #             last_updated_at=coin_data.get("last_updated_at"),
    #         )
    #         if simple_price.price is not None:
    #             return float(simple_price.price)
    #         return None
    #     except (json.JSONDecodeError, KeyError, ValueError, TypeError):
    #         return None

    # async def get_index_str(self, crypto_currency_input: str, vs_currency: str = "eur") -> str:
    #     result = await self.get_index(crypto_currency_input, vs_currency)
    #     if result is None:
    #         return f'Could not find price for "{crypto_currency_input}". \nPlease enter correct id.'
    #     currency_display = get_currency_display(vs_currency)
    #     return f"{crypto_currency_input.capitalize()}: {result:.2f} {currency_display}"

    async def get_index(self, crypto_symbol: str, vs_currency_symbol: str = "eur") -> str:
        crypto_symbol = crypto_symbol.upper().strip()
        vs_currency_symbol = vs_currency_symbol.upper().strip()
        ticker = yf.Ticker(f"{crypto_symbol}-{vs_currency_symbol}")
        current_price = ticker.fast_info["last_price"]
        if current_price is None:
            return f'Could not find price for "{crypto_symbol}". \nPlease enter correct id.'
        currency_display = get_currency_display(vs_currency_symbol)
        return f"{crypto_symbol.upper()}: {current_price:.2f} {currency_display}"

    async def fetch_ticker_prices(self, tickers: List[str]) -> Dict[str, TickerResult]:
        """
        Fetches prices and returns a dictionary mapping Ticker Strings -> TickerResult objects.
        """
        if not tickers:
            return {}

        # Normalize inputs
        clean_tickers = [t.upper().strip() for t in tickers]
        results: Dict[str, TickerResult] = {}
        failed_tickers = []

        # --- PHASE 1: Direct Download ---
        data_direct = yf.download(
            " ".join(clean_tickers),
            period="5d",
            interval="1m",
            group_by="ticker",
            progress=False,
            threads=True,
        )

        is_multi_direct = isinstance(data_direct.columns, pd.MultiIndex)

        # Helper: Extract single float price from dataframe
        def extract_price(df, tick, is_multi) -> Optional[float]:
            series = None
            if is_multi:
                if tick in df.columns:
                    series = df[tick]["Close"]
            elif "Close" in df.columns:
                series = df["Close"]

            if series is not None:
                valid = series.dropna()
                if not valid.empty:
                    return float(valid.iloc[-1])
            return None

        # Process Initial Results
        for tick in clean_tickers:
            price = extract_price(data_direct, tick, is_multi_direct)

            # Simple parse: "BTC-EUR" -> currency="EUR", "AAPL" -> currency="USD"
            parts = tick.split("-")
            currency = parts[1] if len(parts) > 1 else "USD"

            if price is not None:
                results[tick] = TickerResult(
                    symbol=tick, price=price, currency=currency, found=True, is_calculated=False
                )
            else:
                failed_tickers.append(tick)
                # Create a 'failed' result initially
                results[tick] = TickerResult(
                    symbol=tick, price=None, currency=currency, found=False
                )

        # --- PHASE 2: Fallback Logic (USD Conversion) ---
        fallback_map = {}
        needed_fallback_tickers = set()

        for fail_tick in failed_tickers:
            parts = fail_tick.split("-")
            # Only fallback if it's a crypto pair (X-Y) and target isn't USD
            if len(parts) > 1 and parts[1] != "USD":
                base, quote = parts
                base_usd = f"{base}-USD"
                forex = f"{quote}=X"

                fallback_map[fail_tick] = {"base_usd": base_usd, "forex": forex}
                needed_fallback_tickers.add(base_usd)
                needed_fallback_tickers.add(forex)

        if needed_fallback_tickers:
            data_fallback = yf.download(
                " ".join(needed_fallback_tickers),
                period="5d",
                interval="1m",
                group_by="ticker",
                progress=False,
                threads=True,
            )
            is_multi_fallback = isinstance(data_fallback.columns, pd.MultiIndex)

            for original_tick, reqs in fallback_map.items():
                price_base_usd = extract_price(data_fallback, reqs["base_usd"], is_multi_fallback)
                rate_forex = extract_price(data_fallback, reqs["forex"], is_multi_fallback)

                if price_base_usd and rate_forex:
                    # Math: BTC(USD) * EUR=X(rate)
                    final_price = price_base_usd * rate_forex

                    # Update the existing result object in place
                    results[original_tick].price = final_price
                    results[original_tick].found = True
                    results[original_tick].is_calculated = True

        return results

    def format_ticker_message(
        self, data: Dict[str, TickerResult], ordered_tickers: List[str]
    ) -> str:
        if not data:
            return "No tickers provided."

        final_output = []

        for tick in ordered_tickers:
            key = tick.upper().strip()
            res = data.get(key)

            # 1. Check if result exists and was found
            if not res or not res.found or res.price is None:
                final_output.append(f"{key}: data not found")
                continue

            # 2. Handle Currency Display (Symbol vs Code)
            try:
                # Assuming get_currency_display is available in your scope
                curr_symbol = get_currency_display(res.currency)
            except NameError:
                curr_symbol = res.currency

            # 3. Format Price
            calc_note = " (calc)" if res.is_calculated else ""
            final_output.append(f"{key}: {res.price:.2f} {curr_symbol}{calc_note}")

        return "\n".join(final_output)

    async def get_prices(self, tickers: list[str]) -> str:
        """
        Input: ["BTC-EUR", "ETH-USD", "SOL-GBP"]
        """
        price_data = await self.fetch_ticker_prices(tickers)
        message = self.format_ticker_message(price_data, tickers)
        return message

    async def get_coingecko_supported_vs_currencies(self) -> list[str]:
        url = f"{self.COINGECKO_BASE_URL}/simple/supported_vs_currencies"
        response = await self.client.get(url)
        json_obj = json.loads(response.text)
        if not isinstance(json_obj, list):
            return []
        return [str(currency) for currency in json_obj]

    async def get_yfinance_supported_crypto_currencies(self) -> list[Cryptocurrency]:
        s = Screener()
        data = s.get_screeners("all_cryptocurrencies_us", count=250)
        crypto_dicts = data["all_cryptocurrencies_us"]["quotes"]
        supported_crypto_currencies = []
        for d in crypto_dicts:
            raw_symbol = d["symbol"]
            clean_symbol = raw_symbol.replace("-USD", "")
            raw_name = d.get("shortName", "")
            clean_name = raw_name.split(" USD")[0]
            supported_crypto_currencies.append(Cryptocurrency(symbol=clean_symbol, name=clean_name))
        return supported_crypto_currencies

    async def get_notification_index(
        self, crypto_symbol: str, vs_symbol: str = "USDT"
    ) -> float | None:
        url = f"{self.BINANCE_BASE_URL}/ticker/price?symbol={crypto_symbol.upper()}{vs_symbol.upper()}"
        try:
            response = await self.client.get(url)
            json_obj = json.loads(response.text)
            price_str = json_obj.get("price")
            if price_str is not None:
                return float(price_str)
            return None
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            return None
