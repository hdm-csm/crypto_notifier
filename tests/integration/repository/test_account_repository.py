from app.repository.account_repository import AccountRepository
from app.models.schemas import PlatformType, VsCurrency


def setup_dummy_currency(db_session) -> int:
    """Helper function to create a dummy currency and return its ID."""
    currency = VsCurrency(symbol="USD", name="US Dollar")
    db_session.add(currency)
    db_session.commit()
    return currency.id


def test_create_and_find_account(db_session):
    # Setup
    currency_id = setup_dummy_currency(db_session)
    repo = AccountRepository()
    user_id = "12345"
    platform = PlatformType.DISCORD

    # 1. Account erstellen
    new_account = repo.create(db_session, platform, user_id, selected_vs_currency_id=currency_id)
    assert new_account is not None
    assert new_account.platform_user_id == "12345"

    # 2. Account wiederfinden
    found_account = repo.find_by_platform_and_id(db_session, platform, user_id)
    assert found_account is not None
    assert found_account.platform_user_id == user_id
    assert found_account.platform == platform


def test_find_by_platform_and_id_found(db_session):
    """Test that find_by_platform_and_id returns an account when it exists."""
    # Setup
    currency_id = setup_dummy_currency(db_session)
    repo = AccountRepository()
    user_id = "discord_user_123"
    platform = PlatformType.DISCORD

    # Create an account
    created_account = repo.create(db_session, platform, user_id, currency_id)
    db_session.commit()

    # Find the account
    found_account = repo.find_by_platform_and_id(db_session, platform, user_id)

    # Assertions
    assert found_account is not None
    assert found_account.id == created_account.id
    assert found_account.platform == platform
    assert found_account.platform_user_id == user_id
    assert found_account.selected_vs_currency_id == currency_id


def test_find_by_platform_and_id_not_found(db_session):
    """Test that find_by_platform_and_id returns None when account does not exist."""
    # Setup
    repo = AccountRepository()
    platform = PlatformType.DISCORD
    non_existent_user_id = "non_existent_user"

    # Find non-existent account
    found_account = repo.find_by_platform_and_id(db_session, platform, non_existent_user_id)

    # Assertions
    assert found_account is None


def test_find_by_platform_and_id_different_platforms(db_session):
    """Test that find_by_platform_and_id distinguishes between different platforms."""
    # Setup
    currency_id = setup_dummy_currency(db_session)
    repo = AccountRepository()
    user_id = "user_123"

    # Create accounts on different platforms with the same user ID
    discord_account = repo.create(db_session, PlatformType.DISCORD, user_id, currency_id)
    telegram_account = repo.create(db_session, PlatformType.TELEGRAM, user_id, currency_id)
    db_session.commit()

    # Find Discord account
    found_discord = repo.find_by_platform_and_id(db_session, PlatformType.DISCORD, user_id)
    assert found_discord is not None
    assert found_discord.id == discord_account.id
    assert found_discord.platform == PlatformType.DISCORD

    # Find Telegram account
    found_telegram = repo.find_by_platform_and_id(db_session, PlatformType.TELEGRAM, user_id)
    assert found_telegram is not None
    assert found_telegram.id == telegram_account.id
    assert found_telegram.platform == PlatformType.TELEGRAM

    # Verify they are different accounts
    assert found_discord.id != found_telegram.id


def test_find_by_platform_and_id_multiple_users_same_platform(db_session):
    """Test that find_by_platform_and_id returns the correct account when multiple users exist on the same platform."""
    # Setup
    currency_id = setup_dummy_currency(db_session)
    repo = AccountRepository()
    platform = PlatformType.DISCORD
    user_id_1 = "user_1"
    user_id_2 = "user_2"

    # Create multiple accounts on the same platform
    account_1 = repo.create(db_session, platform, user_id_1, currency_id)
    account_2 = repo.create(db_session, platform, user_id_2, currency_id)
    db_session.commit()

    # Find first account
    found_account_1 = repo.find_by_platform_and_id(db_session, platform, user_id_1)
    assert found_account_1 is not None
    assert found_account_1.id == account_1.id
    assert found_account_1.platform_user_id == user_id_1

    # Find second account
    found_account_2 = repo.find_by_platform_and_id(db_session, platform, user_id_2)
    assert found_account_2 is not None
    assert found_account_2.id == account_2.id
    assert found_account_2.platform_user_id == user_id_2
