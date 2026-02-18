from __future__ import annotations

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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.enums import PlatformType, NotificationDirection


favorites_table = Table(
    "favorites",
    Base.metadata,
    Column("account_id", Integer, ForeignKey("accounts.id"), primary_key=True),
    Column("cryptocurrency_id", Integer, ForeignKey("cryptocurrencies.id"), primary_key=True),
)


class VsCurrency(Base):
    __tablename__ = "vs_currencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "crypto_symbol",
            "vs_symbol",
            "direction",
            "target_price",
            name="uq_account_crypto_vs_direction_target",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    crypto_symbol: Mapped[str] = mapped_column(String(255))
    vs_symbol: Mapped[str] = mapped_column(String(255))
    direction: Mapped[NotificationDirection] = mapped_column(Enum(NotificationDirection))
    target_price: Mapped[float] = mapped_column(Float)
    already_hit: Mapped[bool] = mapped_column(default=False)

    account: Mapped[Account] = relationship("Account", back_populates="notifications")


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("platform", "platform_user_id", name="uq_platform_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False)
    platform_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    selected_vs_currency_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vs_currencies.id"), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    notifications: Mapped[list[Notification]] = relationship(
        "Notification", back_populates="account"
    )
    selected_vs_currency: Mapped[VsCurrency] = relationship(
        "VsCurrency", foreign_keys=[selected_vs_currency_id]
    )
    favorite_cryptos: Mapped[list[Cryptocurrency]] = relationship(
        "Cryptocurrency", secondary=favorites_table, back_populates="favorited_by"
    )


class Cryptocurrency(Base):
    __tablename__ = "cryptocurrencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(25), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))

    favorited_by: Mapped[list[Account]] = relationship(
        "Account", secondary=favorites_table, back_populates="favorite_cryptos"
    )
