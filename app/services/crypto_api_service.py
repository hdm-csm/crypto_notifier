import logging
from math import e
from typing import List, Dict, Optional, Union
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


class CryptoApiService:
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"  # Rate Limit = 10K requests/month
    # BINANCE_BASE_URL = "https://api.binance.com/api/v3"  # Unlimited requests

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_top_crypto_currencies(
        self, amount: int, vs_currency: str
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
        coins = [CoinMarketData(**coin_data) for coin_data in json_obj]
        return coins

    async def get_top_crypto_currencies_str(self, amount: int, vs_currency: str) -> str:
        coins = await self.get_top_crypto_currencies(amount, vs_currency)
        currency_display = get_currency_display(vs_currency)
        message = f"Top {amount} by market cap ({currency_display})\n\n"
        for coin in coins:
            medal = (
                "🥇"
                if coin.market_cap_rank == 1
                else (
                    "🥈"
                    if coin.market_cap_rank == 2
                    else ("🥉" if coin.market_cap_rank == 3 else f"#{coin.market_cap_rank}")
                )
            )
            market_cap = coin.market_cap
            if market_cap >= 1_000_000_000:
                market_cap_str = f"{market_cap / 1_000_000_000:.1f}B"
            elif market_cap >= 1_000_000:
                market_cap_str = f"{market_cap / 1_000_000:.1f}M"
            else:
                market_cap_str = f"{market_cap:,.0f}"
            message += f"{medal}  {coin.name} ({coin.symbol.upper()})\n"
            message += f"     Price: {coin.current_price:,.2f} · Cap: {market_cap_str}\n\n"
        return message

    # async def get_index(self, crypto_symbol: str, vs_currency_symbol: str ) -> str:
    #     crypto_symbol = crypto_symbol.upper().strip()
    #     vs_currency_symbol = vs_currency_symbol.upper().strip()
    #     ticker_str = f"{crypto_symbol}-{vs_currency_symbol}"
    #     ticker = yf.Ticker(ticker_str)
    #     try:
    #         logging.info(f"Fetching price for {ticker_str}...")
    #         ticker_str = "BTC-"
    #         lookup = yf.Lookup(ticker_str)
    #         # Get all search results as a pandas DataFrame
    #         results_df = lookup.all  # or lookup.get_all()
    #         logging.info(results_df.shape)
    #         # Select only the most readable/useful columns
    #         clean_df = results_df[["shortName", "quoteType", "exchange", "regularMarketPrice"]]

    #         # Log only the top 5 results, keeping the index (the ticker symbol) visible
    #         logging.info(f"Top 5 Lookup Results:\n{clean_df.head(25).to_markdown()}")

    #         current_price = ticker.fast_info["last_price"]
    #     except Exception as e:
    #         logging.error(e)
    #         return f"❌ An error occurred while fetching price data for {crypto_symbol}:\n {e}"
    #     if current_price is None:
    #         return f"❌ No price data found for {crypto_symbol}."
    #     currency_display = get_currency_display(vs_currency_symbol)
    #     return f"{crypto_symbol.upper()}: {current_price:.2f} {currency_display}"

    async def fetch_formatted_ticker_price(
        self, crypto_symbol: str, vs_currency_symbol: str
    ) -> str:
        crypto_symbol = crypto_symbol.upper().strip()
        vs_currency_symbol = vs_currency_symbol.upper().strip()
        ticker = f"{crypto_symbol}-{vs_currency_symbol}"
        price_value: str = "?"
        try:
            price = yf.Ticker(ticker).fast_info["last_price"]
            price_value = str(price)
        except Exception:
            price_value = self._get_fallback_converted_price(ticker)
        return f"{crypto_symbol.upper()}: {price_value} {get_currency_display(vs_currency_symbol)}"

    # Dict[str, str] = Dict[crypto_symbol, vs_currency_symbol]
    async def fetch_ticker_prices(self, tickers: Dict[str, str]) -> Dict[str, str]:
        if not tickers:
            return {}
        results: Dict[str, str] = {}
        for ticker in tickers:
            results[ticker] = await self.fetch_formatted_ticker_price(ticker, tickers[ticker])
        return results

    def _get_fallback_converted_price(self, ticker: str) -> str:
        parts = ticker.split("-")
        base_symbol = parts[0]
        vs_currency = parts[1] if len(parts) > 1 else "USD"
        only_usd_message = "⚠️ Could only find USD price: {}-USD = ${:,.2f} USD."
        try:
            usd_pair = f"{base_symbol}-USD"
            usd_price = yf.Ticker(usd_pair).fast_info["last_price"]
            if vs_currency in ["USD", "USDT"]:
                return only_usd_message.format(base_symbol, usd_price)
        except Exception:
            return f"{base_symbol} is not a valid cryptocurrency symbol."
        try:
            fx_pair = f"USD{vs_currency}=X"
            fx_rate = yf.Ticker(fx_pair).fast_info["last_price"]
            calculated_price = usd_price * fx_rate
            return str(calculated_price)
        except Exception:
            return only_usd_message.format(base_symbol, usd_price)

    async def get_prices(self, tickers: list[str]) -> str:
        """
        Input: ["BTC-EUR", "ETH-USD", "SOL-GBP"]
        """
        price_data = await self.fetch_ticker_prices(tickers)
        # message = self.format_ticker_message(price_data, tickers)
        message = price_data
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
