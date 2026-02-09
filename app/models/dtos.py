from dataclasses import dataclass
from typing import Optional, Any, Dict, List


@dataclass
class SimpleCoinPrice:
    """Simple price response from /simple/price endpoint"""

    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    last_updated_at: Optional[int] = None


@dataclass
class CoinData:
    """Complete CoinGecko API response for a single cryptocurrency"""

    # Core identification fields
    id: str
    symbol: str
    name: str
    web_slug: Optional[str] = None
    asset_platform_id: Optional[str] = None

    # Blockchain info
    platforms: Optional[Dict[str, Any]] = None
    detail_platforms: Optional[Dict[str, Any]] = None
    block_time_in_minutes: Optional[int] = None
    hashing_algorithm: Optional[str] = None

    # Categorization
    categories: Optional[List[str]] = None
    preview_listing: Optional[bool] = None
    public_notice: Optional[str] = None
    additional_notices: Optional[List[str]] = None

    # Localization & descriptions
    localization: Optional[Dict[str, str]] = None
    description: Optional[Dict[str, str]] = None
    links: Optional[Dict[str, Any]] = None
    image: Optional[Dict[str, str]] = None
    country_origin: Optional[str] = None
    genesis_date: Optional[str] = None

    # Sentiment
    sentiment_votes_up_percentage: Optional[float] = None
    sentiment_votes_down_percentage: Optional[float] = None

    # Market data
    market_cap_rank: Optional[int] = None
    market_cap_rank_with_rehypothecated: Optional[int] = None
    watchlist_portfolio_users: Optional[int] = None
    market_data: Optional[Dict[str, Any]] = None

    # Community & developer data
    community_data: Optional[Dict[str, Any]] = None
    developer_data: Optional[Dict[str, Any]] = None
    status_updates: Optional[List[Any]] = None
    last_updated: Optional[str] = None
    tickers: Optional[List[Dict[str, Any]]] = None


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
