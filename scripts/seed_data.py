# scripts/seed_data.py
from app.db import Session_Factory, engine
from app.models import (
    Base,
    Account,
    Cryptocurrency,
    Notification,
    PlatformType,
    NotificationDirection,
)
from sqlalchemy import inspect


def create_tables_if_not_exist():
    """Create tables if they don't exist"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "accounts" not in existing_tables or "cryptocurrencies" not in existing_tables:
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created")
    else:
        print("✓ Tables already exist")


def seed():
    db = Session_Factory()

    try:

        # First, create tables if they don't exist
        create_tables_if_not_exist()

        # Check if data already exists to avoid duplicates
        existing_accounts = db.query(Account).count()
        if existing_accounts > 0:
            print(f"✓ Database already contains {existing_accounts} records")
            db.close()
            return

        # Insert seed data
        btc = Cryptocurrency(symbol="BTC", fullName="Bitcoin")
        eth = Cryptocurrency(symbol="ETH", fullName="Ethereum")
        sol = Cryptocurrency(symbol="SOL", fullName="Solana")

        db.add_all([btc, eth, sol])

        discord_user = Account(platform=PlatformType.Discord, platformId="discord_user_12345")
        telegram_user = Account(platform=PlatformType.Telegram, platformId="telegram_chat_67890")

        db.add(discord_user)
        db.add(telegram_user)

        discord_user.favorite_cryptos.append(btc)
        discord_user.favorite_cryptos.append(eth)
        telegram_user.favorite_cryptos.append(sol)

        notification_1 = Notification(
            account=discord_user,
            cryptocurrency=btc,
            targetPrice=60000.0,
            direction=NotificationDirection.above,
        )

        db.add(notification_1)

        db.commit()
        print("✓ Seed data inserted")

    except Exception as e:
        print(f"An error occurred during seeding: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
