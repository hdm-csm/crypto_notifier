import discord
from discord.ext import commands
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import io
import logging
from app.bots.discord.custom_context import CustomContext
from yahooquery import Screener


class ChartsCog(commands.Cog):
    """Cryptocurrency charts cog for displaying price charts."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def get_chart_buffer(symbol: str, period: str, interval: str) -> io.BytesIO | None:
        """
        Fetches data and generates a chart image in memory.
        """
        try:
            ticker = f"{symbol.upper()}-USD"

            # lookup = yf.Lookup()
            # cryptos = lookup.get_cryptocurrency(count=500)
            # for idx, crypto in enumerate(cryptos, 1):
            #     logging.info(f"{idx}: {crypto}")

            s = Screener()
            data = s.get_screeners("all_cryptocurrencies_us", count=100)
            dicts = data["all_cryptocurrencies_us"]["quotes"]
            symbols = [d["symbol"] for d in dicts]

            print(symbols)  # Returns a list like ['BTC-USD', 'ETH-USD', ...]

            print("\n ------------------------------------------------- \n")

            from yahooquery import search

            # Search for anything matching "BTC"
            results = search("BTC")

            # Filter for quotes that are likely currency pairs
            # (Yahoo usually categorizes them as 'CRYPTOCURRENCY' or 'CURRENCY')
            btc_pairs = [
                item
                for item in results["quotes"]
                if "symbol" in item and item["symbol"].startswith("BTC-")
            ]

            for pair in btc_pairs:
                print(f"{pair['symbol']}: {pair.get('shortname', 'No Name')}")

            print("\n ------------------------------------------------- \n")

            # ticker = AAPL, BTC-USD, ^GSPC (indices), CURRENCYPAIR=X, GC=F
            data = yf.download(ticker, period=period, interval=interval, progress=False)
            logging.info(f"Downloaded data shape: {data.shape}, empty: {data.empty}")

            if data.empty:
                logging.warning(f"No data returned for ticker: {ticker}")
                return None

            # Handle case where single ticker returns Series instead of DataFrame
            if not isinstance(data, type(pd.DataFrame())):
                logging.error(f"Unexpected data type: {type(data)}, expected DataFrame")
                return None

            # Clean data: drop NaN values and ensure numeric types
            data = data.dropna()
            if data.empty:
                logging.warning(f"No valid data after dropping NaN for ticker: {ticker}")
                return None

            # Handle MultiIndex columns (when yfinance returns multiple tickers)
            if isinstance(data.columns, pd.MultiIndex):
                logging.info(
                    f"MultiIndex columns detected: {data.columns.tolist()}"
                )  # ('Close', 'BTC-USD')
                data.columns = data.columns.get_level_values(0)  # Close
                data = data.loc[:, ~data.columns.duplicated()]  # Remove duplicates

            logging.info(f"Data after cleaning: shape={data.shape}, dtypes={data.dtypes.to_dict()}")

            buffer = io.BytesIO()  # create RAM space

            # https://github.com/matplotlib/mplfinance/blob/master/examples/styles.ipynb
            # Use nightclouds as base for dark mode, then customize market colors
            market_colors = mpf.make_marketcolors(up="#00ff00", down="#ff0000", inherit=True)
            style = mpf.make_mpf_style(base_mpf_style="nightclouds", marketcolors=market_colors)

            # 4. Generate the plot
            # We use savefig=buffer to save to RAM instead of disk
            mpf.plot(
                data,
                type="candle",
                volume=True,
                title=f"{ticker} ({period})",
                style=style,
                savefig=dict(fname=buffer, dpi=100, bbox_inches="tight", pad_inches=0.1),
            )

            buffer.seek(0)  # moves the pointer back to the start of the file in RAM
            logging.info(f"Successfully generated chart for {ticker}")
            return buffer
        except Exception as e:
            logging.error(f"Error generating chart for {symbol}: {e}", exc_info=True)
            return None

    # Schlusskurs vom Freitag !!!

    @staticmethod
    def get_curs() -> None:
        import yfinance as yf

        # Liste gängiger ISO-Währungscodes (Fiat)
        currencies = [
            "USD",
            "EUR",
            "JPY",
            "GBP",
            "CHF",
            "CAD",
            "AUD",
            "NZD",
            "CNY",
            "INR",
            "RUB",
            "KRW",
            "HKD",
            "SGD",
            "SEK",
            "TRY",
            "ZAR",
            "BRL",
            "MXN",
            "PLN",
            "NOK",
            "DKK",
            "IDR",
            "HUF",
            "CZK",
            "ILS",
            "CLP",
            "PHP",
            "AED",
            "COP",
            "SAR",
            "MYR",
            "RON",
        ]

        # Wir bauen die Ticker-Liste (z.B. "BTC-EUR", "BTC-JPY")
        tickers_to_check = [f"BTC-{curr}" for curr in currencies]

        print("Überprüfe Verfügbarkeit auf Yahoo Finance (das dauert kurz)...")

        # Wir versuchen, Daten für alle herunterzuladen (nur heute, um Existenz zu prüfen)
        # group_by='ticker' sorgt dafür, dass wir die Struktur leichter prüfen können
        data = yf.download(tickers_to_check, period="1d", group_by="ticker", progress=False)

        valid_pairs = []

        # Wir iterieren durch die Ergebnisse
        for ticker in tickers_to_check:
            try:
                # Wenn wir 'Close'-Daten für diesen Ticker haben und diese nicht leer sind
                if ticker in data.columns.levels[0]:
                    # Prüfen, ob der letzte Wert keine 'NaN' (Not a Number) ist
                    last_price = data[ticker]["Close"].iloc[-1]
                    if not isinstance(last_price, float) or last_price > 0:
                        valid_pairs.append(ticker)
            except Exception:
                continue

        print(f"\n--- Gefundene BTC-Paare ({len(valid_pairs)}) ---")
        for pair in valid_pairs:
            print(pair)

    @staticmethod
    def get_crypto_price(crypto_symbol="BTC", target_currency="EUR"):
        """
        Versucht den Krypto-Preis direkt zu holen. Falls nicht verfügbar,
        wird er über USD umgerechnet (Synthetischer Kurs).
        """
        target_currency = target_currency.upper()
        crypto_symbol = crypto_symbol.upper()

        # 1. Versuch: Direktes Paar (z.B. BTC-EUR, BTC-CHF)
        direct_ticker = f"{crypto_symbol}-{target_currency}"
        print(f"--- Prüfe direkten Weg: {direct_ticker} ---")

        data = yf.download(direct_ticker, period="1d", progress=False)

        if not data.empty and len(data) > 0:
            price = data["Close"].iloc[-1]
            # Sicherstellen, dass wir einen Einzelwert haben (kein Series-Objekt)
            if isinstance(price, pd.Series):
                price = price.item()

            print("✅ Direktes Paar gefunden!")
            return price, "Direkt (Live 24/7)"

        # 2. Versuch: Fallback über USD (Synthetisch)
        print("❌ Kein direktes Paar. Starte Umrechnung über USD...")

        # Wir brauchen BTC-USD und den Forex-Kurs (z.B. CHF=X für USD/CHF)
        # Yahoo Forex Ticker sind fast immer "WÄHRUNG=X" für den Preis von 1 USD in Fremdwährung
        usd_pair = f"{crypto_symbol}-USD"
        forex_ticker = f"{target_currency}=X"

        # Batch-Download für Effizienz
        tickers = f"{usd_pair} {forex_ticker}"
        data_mix = yf.download(tickers, period="1d", group_by="ticker", progress=False)

        try:
            # Krypto Preis in USD holen
            price_in_usd = data_mix[usd_pair]["Close"].iloc[-1]

            # Umrechnungskurs holen (Wie viel [Währung] bekomme ich für 1 USD?)
            exchange_rate = data_mix[forex_ticker]["Close"].iloc[-1]

            # Berechnung
            synthetic_price = price_in_usd * exchange_rate

            # Einzelwerte extrahieren
            if hasattr(synthetic_price, "item"):
                synthetic_price = synthetic_price.item()

            print(
                f"✅ Synthetischer Preis berechnet (USD Kurs: {price_in_usd:.2f} * FX Rate: {exchange_rate:.4f})"
            )
            return synthetic_price, "Synthetisch (Forex-Rate evtl. vom Freitag)"

        except KeyError:
            print("❌ Auch der Umweg ist gescheitert. Währungscodes prüfen!")
            return None, None

    @commands.command(name="chart")
    async def chart(self, ctx: CustomContext, symbol: str, time_option: str = "today") -> None:
        """
        Display a cryptocurrency price chart.
        Usage: /chart btc today
        Options: today, yesterday, week, month, year
        """

        # Map user friendly words to yfinance API periods/intervals
        time_map = {
            "today": {"period": "1d", "interval": "15m"},  # High res for 1 day
            "yesterday": {"period": "2d", "interval": "30m"},  # 2 days to see comparison
            "week": {"period": "7d", "interval": "60m"},
            "month": {"period": "1mo", "interval": "1d"},
            "year": {"period": "1y", "interval": "1wk"},
        }

        # Default to "today" if option not found
        selection = time_map.get(time_option.lower(), time_map["today"])

        await ctx.send(f"Generating **{symbol.upper()}** chart for **{time_option}**...")

        # yfinance and mplfinance are blocking, so we run the chart generation in an executor to avoid blocking the event loop
        buffer = await self.bot.loop.run_in_executor(
            None, self.get_chart_buffer, symbol, selection["period"], selection["interval"]
        )
        if buffer:
            # Send the buffer as a Discord File
            file = discord.File(fp=buffer, filename=f"{symbol}_chart.png")
            await ctx.send(file=file)
        else:
            await ctx.send(f"❌ Could not find data for symbol: {symbol}")

        # await self.bot.loop.run_in_executor(None, self.get_curs)

        # price, method = await self.bot.loop.run_in_executor(
        #     None, self.get_crypto_price, "BTC", "EUR"
        # )
        # if price:
        #     print(f"Ergebnis BTC in EUR: {price:,.2f} ({method})\n")

        # # 2. Test: Eine Währung aus Ihrem Log, die gefehlt hat (CHF - Schweiz)
        # price, method = await self.bot.loop.run_in_executor(
        #     None, self.get_crypto_price, "BTC", "CHF"
        # )
        # if price:
        #     print(f"Ergebnis BTC in CHF: {price:,.2f} ({method})\n")

        # # 3. Test: Eine weitere fehlende (SEK - Schweden)
        # price, method = await self.bot.loop.run_in_executor(
        #     None, self.get_crypto_price, "BTC", "SEK"
        # )
        # if price:
        #     print(f"Ergebnis BTC in SEK: {price:,.2f} ({method})\n")
