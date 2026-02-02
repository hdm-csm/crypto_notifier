from app.repository.account_repository import AccountRepository
from app.models.schemas import PlatformType


def test_create_and_find_account(db_session):
    # Setup
    repo = AccountRepository()
    user_id = "12345"
    platform = PlatformType.DISCORD

    # 1. Account erstellen
    new_account = repo.create(db_session, platform, user_id)
    assert new_account is not None
    assert new_account.platform_user_id == "12345"

    # 2. Account wiederfinden
    found_account = repo.find_by_platform_and_id(db_session, platform, user_id)
    assert found_account is not None
    assert found_account.platform_user_id == user_id
    assert found_account.platform == platform


def test_exists_check(db_session):
    repo = AccountRepository()

    assert repo.exists(db_session, PlatformType.TELEGRAM, "999") is False

    # Account anlegen
    repo.create(db_session, PlatformType.TELEGRAM, "999")

    assert repo.exists(db_session, PlatformType.TELEGRAM, "999") is True
