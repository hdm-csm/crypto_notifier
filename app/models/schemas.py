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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False)
    platform_user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    preferred_fiat_currency_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fiat_currencies.id"), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="account"
    )
    preferred_fiat_currency: Mapped["FiatCurrency"] = relationship("FiatCurrency")

    favorite_cryptos: Mapped[list["Cryptocurrency"]] = relationship(
        "Cryptocurrency", secondary=favorites_table, back_populates="favorited_by"
    )


class Cryptocurrency(Base):
    __tablename__ = "cryptocurrencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="cryptocurrency"
    )

    favorited_by: Mapped[list["Account"]] = relationship(
        "Account", secondary=favorites_table, back_populates="favorite_cryptos"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    cryptocurrency_id: Mapped[int] = mapped_column(Integer, ForeignKey("cryptocurrencies.id"))
    target_price: Mapped[float] = mapped_column(Float)
    direction: Mapped[NotificationDirection] = mapped_column(Enum(NotificationDirection))

    account: Mapped["Account"] = relationship("Account", back_populates="notifications")
    cryptocurrency: Mapped["Cryptocurrency"] = relationship(
        "Cryptocurrency", back_populates="notifications"
    )


class FiatCurrency(Base):
    __tablename__ = "fiat_currencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    short_name: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
