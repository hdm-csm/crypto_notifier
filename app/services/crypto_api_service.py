import asyncio
import logging
import httpx
import json
from yahooquery import Screener
from app.models.dtos import CoinMarketData, CryptoPrice
from app.models.schemas import Cryptocurrency
from app.models.typealiases import CryptoSymbolStr, VsCurrencySymbolStr
from app.utils.functions import get_currency_display
from config.config import Config
import yfinance as yf
import pandas as pd


COINGECKO_API_KEY = Config.COINGECKO_API_KEY


class CryptoApiService:
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"  # Rate Limit = 10K requests/month

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_top_crypto_currencies(
        self, amount: int, vs_currency: str
    ) -> list[CoinMarketData]:
        amount = max(1, min(amount, 100))
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
            message += f"     Price: {coin.current_price:,.2f} {currency_display} · Cap: {market_cap_str}\n\n"
        return message

    async def fetch_ticker_price(self, crypto_symbol: str, vs_currency_symbol: str) -> CryptoPrice:
        """
        Fetches the latest price for a single crypto pair using yfinance fast_info.
        Returns a populated CryptoPrice dataclass.
        """
        c = crypto_symbol.upper().strip()
        v = vs_currency_symbol.upper().strip()

        def _get_fast_price(ticker_str: str) -> float | None:
            try:
                price = yf.Ticker(ticker_str).fast_info.last_price
                if price is not None:
                    return float(price)
                return None
            except Exception:
                return None

        direct_ticker = f"{c}-{v}"
        direct_price = await asyncio.to_thread(_get_fast_price, direct_ticker)
        if direct_price is not None:
            return CryptoPrice(price=direct_price)
        # If the target was USD and direct failed, there is no fallback left
        if v == "USD":
            return CryptoPrice(price=0.0, error=True)
        # Attempt B: Direct currency failed, fallback to USD base
        usd_ticker = f"{c}-USD"
        usd_price = await asyncio.to_thread(_get_fast_price, usd_ticker)
        if usd_price is not None:
            fx_ticker = f"USD{v}=X"
            fx_price = await asyncio.to_thread(_get_fast_price, fx_ticker)
            if fx_price is not None:
                return CryptoPrice(price=(usd_price * fx_price), self_converted=True)
            else:
                # Attempt C: Forex failed, return USD only
                return CryptoPrice(price=usd_price, only_usd=True)
        # Attempt D: Completely failed (no direct and no USD fallback exist)
        return CryptoPrice(price=0.0, error=True)

    async def fetch_ticker_prices(
        self, ticker_pairs: set[tuple[CryptoSymbolStr, VsCurrencySymbolStr]]
    ) -> list[tuple[CryptoSymbolStr, VsCurrencySymbolStr, CryptoPrice]]:
        """
        Batch fetches prices for multiple crypto pairs.
        Returns a list of tuples: (crypto_symbol, vs_currency, CryptoPrice)
        """
        if not ticker_pairs:
            return []
        cleaned_pairs: set[tuple[CryptoSymbolStr, VsCurrencySymbolStr]] = set()
        all_tickers: set[str] = set()
        for crypto, vs in ticker_pairs:
            c, v = crypto.upper().strip(), vs.upper().strip()
            cleaned_pairs.add((c, v))
            all_tickers.add(f"{c}-{v}")
            if v != "USD":
                all_tickers.update((f"{c}-USD", f"USD{v}=X"))
        yf_ticker_list = list(all_tickers)

        def _fetch_batch() -> pd.DataFrame:
            return yf.download(tickers=yf_ticker_list, period="1d", progress=False)

        df = await asyncio.to_thread(_fetch_batch)
        if df.empty:
            return []
        latest_prices: dict[str, float] = {}
        if isinstance(df.columns, pd.MultiIndex):
            latest_prices = df["Close"].iloc[-1].to_dict()
        else:
            latest_prices = {yf_ticker_list[0]: float(df["Close"].iloc[-1])}

        def get_price(ticker_str: str) -> float:
            val = latest_prices.get(ticker_str, 0.0)
            return float(val) if pd.notna(val) else 0.0

        results = []
        for crypto, vs in cleaned_pairs:
            preferred_ticker = f"{crypto}-{vs}"
            # Attempt A: Direct match available
            direct_price = get_price(preferred_ticker)
            if direct_price > 0:
                results.append((crypto, vs, CryptoPrice(price=direct_price)))
                continue
            usd_price = get_price(f"{crypto}-USD")
            if usd_price > 0:
                fx_price = get_price(f"USD{vs}=X")
                if fx_price > 0:
                    calculated_value = usd_price * fx_price
                    # Attempt B: Fallback logic (Only executes if direct fails and vs != USD)
                    results.append(
                        (crypto, vs, CryptoPrice(price=calculated_value, self_converted=True))
                    )
                else:
                    # Attempt C: Forex failed, return USD only
                    results.append((crypto, vs, CryptoPrice(price=usd_price, only_usd=True)))
            else:
                # Attempt D: Completely failed
                results.append((crypto, vs, CryptoPrice(price=0.0, error=True)))
        return results

    def _get_converted_price(self, crypto_symbol: str, vs_currency_symbol: str) -> str:
        only_usd_message = "⚠️ Could only find USD price: {}-USD = ${:,.2f} USD."
        try:
            usd_pair = f"{crypto_symbol}-USD"
            usd_price = yf.Ticker(usd_pair).fast_info["last_price"]
        except Exception:
            logging.info(f"Unable to fetch {usd_pair}")
            return f"{crypto_symbol} is not a valid cryptocurrency symbol."
        try:
            fx_pair = f"USD{vs_currency_symbol}=X"
            fx_rate = yf.Ticker(fx_pair).fast_info["last_price"]
        except Exception:
            logging.info(f"Unable to fetch {fx_pair} (for currency conversion)")
            return only_usd_message.format(crypto_symbol, usd_price)
        calculated_price = usd_price * fx_rate
        return str(calculated_price)

    async def get_coingecko_supported_vs_currencies(self) -> list[str]:
        url = f"{self.COINGECKO_BASE_URL}/simple/supported_vs_currencies"
        response = await self.client.get(url)
        json_obj = json.loads(response.text)
        if not isinstance(json_obj, list):
            return []
        return [str(currency) for currency in json_obj]

    async def get_yfinance_supported_crypto_currencies(
        self, amount: int = 250
    ) -> list[Cryptocurrency]:
        """
        Fetches a list of MAX 250 supported cryptocurrencies from Yahoo Finance screener.
        """
        amount = max(1, min(amount, 250))  # Ensure amount is between 1 and 250
        try:
            s = Screener()
            data = s.get_screeners("all_cryptocurrencies_us", count=amount)
        except Exception as e:
            logging.error(f"Failed to fetch screener data: {e}")
            return []
        try:
            raw = data["all_cryptocurrencies_us"]
            crypto_dicts: list = raw if isinstance(raw, list) else raw["quotes"]
        except (KeyError, TypeError) as e:
            logging.error(f"Unexpected screener response structure: {e}\ndata={data}")
            return []

        supported_crypto_currencies = []
        for d in crypto_dicts:
            try:
                raw_symbol: str = d["symbol"]
                clean_symbol = raw_symbol.replace("-USD", "").strip()
                if not clean_symbol:
                    continue
                raw_name: str = d.get("shortName") or d.get("longName") or ""
                clean_name = raw_name.split(" USD")[0].strip()
                supported_crypto_currencies.append(
                    Cryptocurrency(symbol=clean_symbol, name=clean_name)
                )
            except (KeyError, TypeError) as e:
                logging.warning(f"Skipping malformed crypto entry {d!r}: {e}")
                continue

        return supported_crypto_currencies
