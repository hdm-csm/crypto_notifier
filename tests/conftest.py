import pytest
import asyncio
from sqlalchemy import create_engine
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


# Datenbank Fixture für Integration Tests
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")

    # Tabellen erstellen
    Base.metadata.create_all(engine)

    # Session erstellen
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    # Aufräumen nach Tests
    session.close()
    Base.metadata.drop_all(engine)
