# app/models.py
from app.db import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Enum,
    ForeignKey,
    Table,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
from dataclasses import dataclass
from typing import Optional


@dataclass
class Coin:
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


class PlatformType(enum.Enum):
    Discord = "Discord"
    Telegram = "Telegram"


class NotificationDirection(enum.Enum):
    above = "above"
    below = "below"


favorites_table = Table(
    "favorites",
    Base.metadata,
    Column("account_id", Integer, ForeignKey("accounts.id"), primary_key=True),
    Column("cryptocurrency_id", Integer, ForeignKey("cryptocurrencies.id"), primary_key=True),
)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False)
    platform_id = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    notifications = relationship("Notification", back_populates="account")

    favorite_cryptos = relationship(
        "Cryptocurrency", secondary=favorites_table, back_populates="favorited_by"
    )


class Cryptocurrency(Base):
    __tablename__ = "cryptocurrencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))

    notifications = relationship("Notification", back_populates="cryptocurrency")

    favorited_by = relationship(
        "Account", secondary=favorites_table, back_populates="favorite_cryptos"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    cryptocurrency_id = Column(Integer, ForeignKey("cryptocurrencies.id"))
    target_price = Column(Float)
    direction: Mapped[NotificationDirection] = mapped_column(Enum(NotificationDirection))

    account = relationship("Account", back_populates="notifications")
    cryptocurrency = relationship("Cryptocurrency", back_populates="notifications")
