# app/models.py
from app.db import Base
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Table, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
import enum

class PlatformType(enum.Enum):
    Discord = "Discord"
    Telegram = "Telegram"

class NotificationDirection(enum.Enum):
    above = "above"
    below = "below"

favorites_table = Table(
    'favorites',
    Base.metadata,
    Column('userId', Integer, ForeignKey('accounts.userId'), primary_key=True),
    Column('cryptoID', Integer, ForeignKey('cryptocurrencies.cryptoId'), primary_key=True)
)

class Account(Base):
    __tablename__ = 'accounts'
    
    userId = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(Enum(PlatformType), nullable=False)
    platformId = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    notifications = relationship("Notification", back_populates="account")
    
    favorite_cryptos = relationship(
        "Cryptocurrency",
        secondary=favorites_table,
        back_populates="favorited_by"
    )

class Cryptocurrency(Base):
    __tablename__ = 'cryptocurrencies'
    
    cryptoId = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(255), unique=True, index=True)
    fullName = Column(String(255))
    
    notifications = relationship("Notification", back_populates="cryptocurrency")
    
    favorited_by = relationship(
        "Account",
        secondary=favorites_table,
        back_populates="favorite_cryptos"
    )

class Notification(Base):
    __tablename__ = 'notifications'
    
    notificationID = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('accounts.userId'))
    cryptoID = Column(Integer, ForeignKey('cryptocurrencies.cryptoId'))
    targetPrice = Column(Float)
    direction = Column(Enum(NotificationDirection))
    
    account = relationship("Account", back_populates="notifications")
    cryptocurrency = relationship("Cryptocurrency", back_populates="notifications")