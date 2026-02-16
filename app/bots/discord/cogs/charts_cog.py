import discord
from discord.ext import commands
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import io
import logging
from app.bots.discord.custom_context import CustomContext


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
            # 1. Fetch data using yfinance
            # Adding "-USD" helps find crypto tickers (e.g., BTC-USD)
            ticker = f"{symbol.upper()}-USD"
            logging.info(
                f"Fetching chart data for ticker: {ticker}, period: {period}, interval: {interval}"
            )

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
                logging.info(f"MultiIndex columns detected: {data.columns.tolist()}")
                # Flatten MultiIndex columns - get the first ticker's data
                data.columns = data.columns.get_level_values(0)
                # Remove duplicate columns if they exist
                data = data.loc[:, ~data.columns.duplicated()]

            logging.info(f"Data after cleaning: shape={data.shape}, dtypes={data.dtypes.to_dict()}")

            # 2. Setup the memory buffer
            buffer = io.BytesIO()

            # 3. Configure the plot style (Dark theme looks best on Discord)
            # 'binance' style is popular for crypto, or use 'nightclouds'
            mc = mpf.make_marketcolors(
                up="#00ff00", down="#ff0000", edge="inherit", wick="inherit", volume="in"
            )
            s = mpf.make_mpf_style(marketcolors=mc)

            # 4. Generate the plot
            # We use savefig=buffer to save to RAM instead of disk
            mpf.plot(
                data,
                type="candle",
                volume=True,
                title=f"{ticker} ({period})",
                style=s,
                savefig=dict(fname=buffer, dpi=100, bbox_inches="tight", pad_inches=0.1),
            )

            # 5. Reset buffer position to the start so Discord can read it
            buffer.seek(0)
            logging.info(f"Successfully generated chart for {ticker}")
            return buffer
        except Exception as e:
            logging.error(f"Error generating chart for {symbol}: {e}", exc_info=True)
            return None

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
            "week": {"period": "5d", "interval": "60m"},
            "month": {"period": "1mo", "interval": "1d"},
            "year": {"period": "1y", "interval": "1wk"},
        }

        # Default to "today" if option not found
        selection = time_map.get(time_option.lower(), time_map["today"])

        await ctx.send(f"Generating **{symbol.upper()}** chart for **{time_option}**...")

        # Run blocking code in an executor to avoid freezing the bot
        buffer = await self.bot.loop.run_in_executor(
            None, self.get_chart_buffer, symbol, selection["period"], selection["interval"]
        )

        if buffer:
            # Send the buffer as a Discord File
            file = discord.File(fp=buffer, filename=f"{symbol}_chart.png")
            await ctx.send(file=file)
        else:
            await ctx.send(f"❌ Could not find data for symbol: {symbol}")
