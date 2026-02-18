import discord
from discord.ext import commands
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import io
import logging
from app.bots.discord.chart_view import ChartView


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

    @commands.command(name="chart")
    async def chart(self, ctx: commands.Context, symbol: str, time_option: str = "1D"):
        """
        Display a cryptocurrency price chart with interactive buttons.
        Usage: /chart btc
        """
        if not symbol:
            await ctx.send("⚠️ Please provide at least one cryptocurrency symbol or name.")
            return
        symbol = symbol.upper()
        time_option = time_option.upper()
        view = ChartView(self.bot, symbol, self.get_chart_buffer, initial_label=time_option)
        config = view.time_map.get(time_option, view.time_map["1D"])
        await ctx.send(f"Fetching **{symbol}** data...", delete_after=1.0)
        buffer = await self.bot.loop.run_in_executor(
            None, self.get_chart_buffer, symbol, config["period"], config["interval"]
        )
        if buffer:
            file = discord.File(fp=buffer, filename=f"{symbol}_chart.png")
            await ctx.send(file=file, view=view)
        else:
            await ctx.send(f"❌ Could not find data for symbol: {symbol}")
