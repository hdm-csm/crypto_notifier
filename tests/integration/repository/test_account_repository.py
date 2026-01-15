from app.repository.account_repository import AccountRepository
from app.models import PlatformType


def test_create_and_find_account(db_session):
    # Setup
    repo = AccountRepository()
    user_id = "12345"
    platform = PlatformType.Discord

    # 1. Account erstellen
    new_account = repo.create(db_session, platform, user_id)
    assert new_account is not None
    assert new_account.platformId == "12345"

    # 2. Account wiederfinden
    found_account = repo.find_by_platform_and_id(db_session, platform, user_id)
    assert found_account is not None
    assert found_account.platformId == user_id
    assert found_account.platform == platform


def test_exists_check(db_session):
    repo = AccountRepository()

    assert repo.exists(db_session, PlatformType.Telegram, "999") is False

    # Account anlegen
    repo.create(db_session, PlatformType.Telegram, "999")

    assert repo.exists(db_session, PlatformType.Telegram, "999") is True
