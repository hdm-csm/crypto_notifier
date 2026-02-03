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
from app.models.enums import PlatformType, NotificationDirection

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
    platform_user_id = Column(String(255), nullable=False, unique=True)
    preferred_fiat_currency_id = Column(Integer, ForeignKey("fiat_currencies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    notifications = relationship("Notification", back_populates="account")
    preferred_fiat_currency = relationship("FiatCurrency")

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


class FiatCurrency(Base):
    __tablename__ = "fiat_currencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String(10), unique=True, index=True)
    full_name = Column(String(255))
