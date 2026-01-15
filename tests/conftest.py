import os
import pytest
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models import Coin


# 1. Event Loop Fixture
# Notwendig für asynchrone Tests in Pytest.
# Es stellt sicher, dass für jeden Test ein neuer Event Loop bereitsteht.
@pytest.fixture(scope="function")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 2. Dummy Coin Fixture
@pytest.fixture
def sample_coin():
    return Coin(
        id="bitcoin",
        symbol="btc",
        name="Bitcoin",
        current_price=50000.0,
        market_cap=1000000,
        market_cap_rank=1,
        image="url",
        fully_diluted_valuation=0,
        total_volume=0,
        high_24h=0,
        low_24h=0,
        price_change_24h=0,
        price_change_percentage_24h=0,
        market_cap_change_24h=0,
        market_cap_change_percentage_24h=0,
        circulating_supply=0,
        total_supply=0,
        max_supply=0,
        ath=0,
        ath_change_percentage=0,
        ath_date="",
        atl=0,
        atl_change_percentage=0,
        atl_date="",
        roi=None,
        last_updated="",
    )


@pytest.fixture(scope="session")
def db_engine():
    db_url = os.getenv("TEST_DATABASE_URL")

    # Fallback: Wenn keine URL da ist, nimm SQLite (für lokales Testen ohne Docker)
    if not db_url:
        db_url = "sqlite:///:memory:"
        print("⚠️  Nutze SQLite In-Memory Datenbank für Tests.")
    else:
        print(f"🚀 Nutze externe Datenbank für Tests: {db_url}")

    # Konfiguration je nach Datenbank-Typ
    connect_args = {}
    if "sqlite" in db_url:
        connect_args = {"check_same_thread": False}

    engine = create_engine(db_url, connect_args=connect_args)

    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


# Datenbank Fixture für Integration Tests
@pytest.fixture(scope="function")
def db_session(db_engine):

    # Verbindung zur DB öffnen
    connection = db_engine.connect()

    # Session an die Connection binden
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    # NACH DEM TEST:
    session.close()

    # Löschen alle Daten hart aus der Datenbank via SQL
    with db_engine.connect() as conn:
        try:
            conn.execute(text("DELETE FROM notifications"))
            conn.execute(text("DELETE FROM favorites"))
            conn.execute(text("DELETE FROM accounts"))
            conn.execute(text("DELETE FROM cryptocurrencies"))
            conn.commit()
        except Exception as e:
            print(f"Fehler beim Bereinigen der DB: {e}")

    connection.close()
