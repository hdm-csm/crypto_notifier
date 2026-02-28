from dataclasses import dataclass
from typing import Optional


@dataclass
class SimpleCoinPrice:
    """Simple price response from /simple/price endpoint"""

    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    last_updated_at: Optional[int] = None


@dataclass
class CoinMarketData:
    id: str
    symbol: str
    name: str
    image: str
    current_price: float
    market_cap: int
    market_cap_rank: int
    fully_diluted_valuation: int
    total_volume: int
    high_24h: float
    low_24h: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap_change_24h: float
    market_cap_change_percentage_24h: float
    circulating_supply: float
    total_supply: float
    max_supply: Optional[float]
    ath: float
    ath_change_percentage: float
    ath_date: str
    atl: float
    atl_change_percentage: float
    atl_date: str
    roi: Optional[str]
    last_updated: str


@dataclass
class TickerResult:
    symbol: str
    price: Optional[float]
    currency: str
    found: bool = False
    is_calculated: bool = False

    def __repr__(self):
        status = f"{self.price:.2f}" if self.price else "No Data"
        return f"<TickerResult {self.symbol}: {status} {self.currency}>"


@dataclass
class CryptoPrice:
    price: float
    self_converted: bool = False
    only_usd: bool = False
    error: bool = False
