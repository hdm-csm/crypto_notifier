import io
import logging
import asyncio
import yfinance as yf
import mplfinance as mpf
import pandas as pd


class ChartService:
    """Service responsible for fetching financial data and generating chart images."""

    def _create_plot(self, crypto_symbol: str, period: str, interval: str) -> io.BytesIO | None:
        """Blocking function that generates the chart image in memory."""
        try:
            ticker = f"{crypto_symbol.upper()}-USD"
            data = yf.download(ticker, period=period, interval=interval, progress=False)

            if data.empty:
                logging.warning(f"No data returned for ticker: {ticker}")
                return None

            if not isinstance(data, pd.DataFrame):
                logging.error(f"Unexpected data type: {type(data)}, expected DataFrame")
                return None

            data = data.dropna()
            if data.empty:
                logging.warning(f"No valid data after dropping NaN for ticker: {ticker}")
                return None

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
                data = data.loc[:, ~data.columns.duplicated()]

            buffer = io.BytesIO()

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
            buffer.seek(0)
            return buffer

        except Exception as e:
            logging.error(f"Error generating chart for {crypto_symbol}: {e}", exc_info=True)
            return None

    async def generate_chart_async(
        self, crypto_symbol: str, period: str, interval: str
    ) -> io.BytesIO | None:
        """Asynchronously generates a chart to prevent blocking the event loop."""
        return await asyncio.to_thread(self._create_plot, crypto_symbol, period, interval)
