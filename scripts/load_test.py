import asyncio
import time
import sys
import os

# Pfad-Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Session_Factory, engine, Base  # noqa: E402
from app.models.schemas import VsCurrency  # noqa: E402
from app.models.enums import PlatformType  # noqa: E402
from app.repository.account_repository import AccountRepository  # noqa: E402
from app.repository.vs_currency_repository import VsCurrencyRepository  # noqa: E402
from app.services.account_lookup_service import AccountLookupService  # noqa: E402

# Konfiguration
NUM_CONCURRENT_USERS = 200
PLATFORM = PlatformType.DISCORD


def setup_database():
    """Erstellt das Schema und notwendige Grunddaten."""
    Base.metadata.create_all(bind=engine)

    with Session_Factory() as session:
        # Basis-Währung für Foreign Key Constraints anlegen
        eur = VsCurrency(id=1, symbol="EUR", name="Euro")
        session.add(eur)
        session.commit()


def teardown_database():
    """Löscht alle Tabellen, um die Test-DB sauber zu hinterlassen."""
    Base.metadata.drop_all(bind=engine)


async def simulate_user_action(user_id: str, account_lookup: AccountLookupService):
    """Einzelne User-Interaktion."""
    start_time = time.time()
    success = False
    error_msg = ""

    try:
        with Session_Factory() as db_session:
            try:
                account = account_lookup.find_or_create_account(
                    db_session=db_session, platform_type=PLATFORM, platform_user_id=user_id
                )
                db_session.commit()
                if account:
                    success = True
            except Exception as e:
                db_session.rollback()
                error_msg = str(e)
    except Exception as e:
        error_msg = str(e)

    duration = time.time() - start_time
    return success, duration, error_msg


async def run_load_test():
    try:
        # 1. Setup
        setup_database()

        print(f"Starte Load Test mit {NUM_CONCURRENT_USERS} Usern...")

        account_repo = AccountRepository()
        vs_currency_repo = VsCurrencyRepository()
        account_lookup = AccountLookupService(account_repo, vs_currency_repo)

        # Einzigartige IDs pro Durchlauf
        timestamp = int(time.time())
        tasks = [
            simulate_user_action(f"load_user_{i}_{timestamp}", account_lookup)
            for i in range(NUM_CONCURRENT_USERS)
        ]

        start_total = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_total

        # Auswertung
        success_count = sum(1 for r in results if r[0])
        avg_time = sum(r[1] for r in results) / len(results) if results else 0

        print("\n" + "=" * 35)
        print("LASTTEST ERGEBNISSE")
        print("=" * 35)
        print(f"Gesamtdauer:     {total_time:.2f}s")
        print(f"Ø Antwortzeit:   {avg_time:.4f}s")
        print(f"Erfolgsquote:    {success_count} / {NUM_CONCURRENT_USERS}")
        print("=" * 35)

    finally:
        # 3. Teardown
        teardown_database()


if __name__ == "__main__":
    asyncio.run(run_load_test())
