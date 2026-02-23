from dataclasses import dataclass
from discord.app_commands import Choice
from typing import Dict


@dataclass
class Timeframe:
    value: str  # The ID used by Discord (e.g., "1D")
    display_name: str  # What the user sees (e.g., "1 Day")
    period: str  # The API period (e.g., "1d")
    interval: str  # The API interval (e.g., "15m")

    @property
    def choice(self) -> Choice:
        """Helper to convert this Timeframe into a Discord Choice."""
        return Choice(name=self.display_name, value=self.value)

    @property
    def api_kwargs(self) -> Dict[str, str]:
        """Helper to return the API arguments."""
        return {"period": self.period, "interval": self.interval}


class ChartConfig:
    """Central registry for all chart timeframes."""

    DAY_1 = Timeframe("1D", "1 Day", "1d", "15m")
    DAYS_5 = Timeframe("5D", "5 Days", "5d", "30m")
    MONTH_1 = Timeframe("1M", "1 Month", "1mo", "1d")  # Note: Standardized to "1M" here
    MONTHS_3 = Timeframe("3M", "3 Months", "3mo", "1d")
    MONTHS_6 = Timeframe("6M", "6 Months", "6mo", "1d")
    YTD = Timeframe("YTD", "Year to Date", "ytd", "1d")
    YEAR_1 = Timeframe("1Y", "1 Year", "1y", "1wk")
    YEARS_5 = Timeframe("5Y", "5 Years", "5y", "1mo")
    ALL = Timeframe("All", "All Time", "max", "3mo")

    @classmethod
    def get_choices(cls) -> list[Choice]:
        """Returns all timeframes formatted for @app_commands.choices"""
        return [v.choice for k, v in cls.__dict__.items() if isinstance(v, Timeframe)]

    @classmethod
    def get_map(cls) -> Dict[str, Dict[str, str]]:
        """Returns the dictionary mapping needed for ChartView"""
        return {v.value: v.api_kwargs for k, v in cls.__dict__.items() if isinstance(v, Timeframe)}
