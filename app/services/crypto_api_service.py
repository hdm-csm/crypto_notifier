from typing import List
import httpx
import json

from yahooquery import Screener
from app.models.dtos import CoinMarketData, SimpleCoinPrice
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

    async def get_indexes(self, crypto_symbols: list[str], vs_currency_symbol: str = "eur") -> str:
        if not crypto_symbols:
            return "No symbols provided."

        vs_currency = vs_currency_symbol.upper().strip()
        results = {}
        failed_symbols = []

        # --- PHASE 1: Try Direct Tickers (e.g. BTC-EUR) ---
        direct_map = {s: f"{s.upper().strip()}-{vs_currency}" for s in crypto_symbols}
        direct_tickers = list(direct_map.values())

        # We use period="5d" to be safe, but "1d" is usually enough for direct crypto pairs (24/7 market)
        data_direct = yf.download(
            " ".join(direct_tickers),
            period="5d",
            interval="1m",
            group_by="ticker",
            progress=False,
            threads=True,
        )

        currency_display = get_currency_display(vs_currency)
        is_multi_direct = isinstance(data_direct.columns, pd.MultiIndex)

        for symbol_raw, ticker_direct in direct_map.items():
            price_found = False
            try:
                # Extract the Series for this specific ticker
                price_series = None
                if is_multi_direct:
                    if ticker_direct in data_direct.columns:
                        price_series = data_direct[ticker_direct]["Close"]
                else:
                    # Handle case where only 1 ticker was requested/returned
                    # If the user asked for 1 symbol, yfinance returns flat columns
                    if "Close" in data_direct.columns:
                        # Double check if the single result matches what we wanted
                        # (If we asked for BTC-EUR and got it, good. If we asked for multiple and got 1, tricky)
                        price_series = data_direct["Close"]

                # Check if we have valid data (not all NaNs)
                if price_series is not None:
                    valid_prices = price_series.dropna()
                    if not valid_prices.empty:
                        last_price = valid_prices.iloc[-1]
                        results[symbol_raw] = (
                            f"{symbol_raw.upper()}: {float(last_price):.2f} {currency_display}"
                        )
                        price_found = True
            except Exception:
                pass  # Fail silently here, add to failed list below

            if not price_found:
                failed_symbols.append(symbol_raw)

        # --- PHASE 2: Fallback Calculation (Only for failed symbols) ---
        if failed_symbols and vs_currency != "USD":
            # 1. Prepare Fallback Tickers
            usd_map = {s: f"{s.upper().strip()}-USD" for s in failed_symbols}
            usd_tickers = list(usd_map.values())

            # Currency conversion tickers
            forex_ticker_std = f"{vs_currency}=X"  # e.g., EUR=X (USD -> EUR)
            forex_ticker_inv = f"{vs_currency}USD=X"  # e.g., XAUUSD=X (Gold -> USD)

            # Download batch: Crypto-USD + Forex rates
            # We MUST use period="5d" here. If it's Sunday, Forex is closed.
            # We need Friday's close for currency, but Sunday's close for Crypto.
            fallback_tickers = usd_tickers + [forex_ticker_std, forex_ticker_inv]
            data_fallback = yf.download(
                " ".join(fallback_tickers),
                period="5d",
                interval="1m",
                group_by="ticker",
                progress=False,
                threads=True,
            )

            is_multi_fallback = isinstance(data_fallback.columns, pd.MultiIndex)

            # Helper to get last price from fallback data
            def get_price_from_data(df, ticker, is_multi):
                series = None
                if is_multi:
                    if ticker in df.columns:
                        series = df[ticker]["Close"]
                elif "Close" in df.columns:
                    series = df["Close"]

                if series is not None:
                    valid = series.dropna()
                    if not valid.empty:
                        return float(valid.iloc[-1])
                return None

            # Get Forex Rates
            rate_std = get_price_from_data(data_fallback, forex_ticker_std, is_multi_fallback)
            rate_inv = get_price_from_data(data_fallback, forex_ticker_inv, is_multi_fallback)

            for symbol_raw in failed_symbols:
                ticker_usd = usd_map[symbol_raw]
                price_usd = get_price_from_data(data_fallback, ticker_usd, is_multi_fallback)

                final_price = None

                if price_usd is not None:
                    # Strategy A: Multiply (USD -> Target) e.g. BTC(90k) * EUR=X(0.95)
                    if rate_std is not None:
                        final_price = price_usd * rate_std

                    # Strategy B: Divide (Target -> USD) e.g. BTC(90k) / XAU(2600)
                    elif rate_inv is not None and rate_inv != 0:
                        final_price = price_usd / rate_inv

                if final_price is not None:
                    results[symbol_raw] = (
                        f"{symbol_raw.upper()}: {final_price:.2f} {currency_display} (calc)"
                    )
                else:
                    results[symbol_raw] = f"{symbol_raw.upper()}: data not found"

        elif failed_symbols and vs_currency == "USD":
            # If target is USD and it failed Phase 1, we can't calculate anything better.
            for s in failed_symbols:
                results[s] = f"{s.upper()}: data not found"

        # Construct final output string in original order
        final_output = []
        for s in crypto_symbols:
            # We key by the raw symbol name
            if s in results:
                final_output.append(results[s])
            else:
                # Should theoretically not happen given logic above
                final_output.append(f"{s}: Error processing")

        return "\n".join(final_output)

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
