# Testen der Business-Logik des Bot Service
# Ziel: Testen der Bot-Befehle (Favoriten hinzufügen/löschen)
import pytest
from unittest.mock import MagicMock, AsyncMock, ANY
from app.services.bot_service import BotService
from app.models import PlatformType, Account, Cryptocurrency


@pytest.fixture
def mock_deps():
    return {
        "account_repo": MagicMock(),
        "fav_repo": MagicMock(),
        "crypto_repo": MagicMock(),
        "api_service": AsyncMock(),
    }


@pytest.fixture
def bot_service(mock_deps, mocker):
    # Mock session_scope context manager
    mock_session = MagicMock()
    mock_scope = mocker.patch("app.services.bot_service.session_scope")
    mock_scope.return_value.__enter__.return_value = mock_session

    return BotService(
        mock_deps["account_repo"],
        mock_deps["fav_repo"],
        mock_deps["crypto_repo"],
        mock_deps["api_service"],
    )


# Testen für das Hinzufügen von Favoriten, Fall success
def test_add_favorite_success(bot_service, mock_deps):
    # Setup
    user_id = "12345"
    crypto_name = "bitcoin"

    mock_account = Account(platform=PlatformType.Discord, platform_id=user_id, favorite_cryptos=[])
    mock_deps["account_repo"].find_by_platform_and_id.return_value = mock_account

    mock_crypto = Cryptocurrency(symbol="BTC", full_name="Bitcoin")
    mock_deps["crypto_repo"].find_by_name_or_symbol.return_value = mock_crypto

    # Execution
    result = bot_service.add_favorite(PlatformType.Discord, user_id, crypto_name)

    # Assertion
    mock_deps["fav_repo"].add_favorite.assert_called_once_with(
        session=ANY, account=mock_account, crypto=mock_crypto
    )
    assert "Saved bitcoin" in result


# Testen für das Hinzufügen von Favoriten, Fall not found
def test_add_favorite_crypto_not_found(bot_service, mock_deps):
    # Setup
    user_id = "12345"
    mock_account = Account(platform=PlatformType.Discord, platform_id=user_id)
    mock_deps["account_repo"].find_by_platform_and_id.return_value = mock_account

    mock_deps["crypto_repo"].find_by_name_or_symbol.return_value = None

    # Execution
    result = bot_service.add_favorite(PlatformType.Discord, user_id, "fantasy-coin")

    # Assertion
    mock_deps["fav_repo"].add_favorite.assert_not_called()
    assert "not found" in result


# Testen für das Hinzufügen von Favoriten, Fall already exists
def test_add_favorite_already_exists(bot_service, mock_deps):
    # Setup
    mock_crypto = Cryptocurrency(symbol="BTC", full_name="Bitcoin")
    mock_account = Account(
        platform=PlatformType.Discord, platform_id="123", favorite_cryptos=[mock_crypto]
    )

    mock_deps["account_repo"].find_by_platform_and_id.return_value = mock_account
    mock_deps["crypto_repo"].find_by_name_or_symbol.return_value = mock_crypto

    # Execution
    result = bot_service.add_favorite(PlatformType.Discord, "123", "bitcoin")

    # Assertion
    mock_deps["fav_repo"].add_favorite.assert_not_called()
    assert "already in your favorites" in result


# Testen für das Entfernen von Favoriten, Fall success
def test_remove_favorite_success(bot_service, mock_deps):
    # Setup
    mock_crypto = Cryptocurrency(symbol="ETH", full_name="Ethereum")
    mock_account = Account(
        platform=PlatformType.Telegram, platform_id="999", favorite_cryptos=[mock_crypto]
    )

    mock_deps["account_repo"].find_by_platform_and_id.return_value = mock_account
    mock_deps["crypto_repo"].find_by_name_or_symbol.return_value = mock_crypto

    # Execution
    result = bot_service.remove_favorite(PlatformType.Telegram, "999", "ethereum")

    # Assertion
    mock_deps["fav_repo"].remove_favorite.assert_called_once()
    assert "Removed ethereum" in result


# Testen für das Entfernen von Favoriten, Fall not in list
def test_remove_favorite_not_in_list(bot_service, mock_deps):
    # Setup
    mock_crypto = Cryptocurrency(symbol="ETH", full_name="Ethereum")
    mock_account = Account(platform=PlatformType.Telegram, favorite_cryptos=[])

    mock_deps["account_repo"].find_by_platform_and_id.return_value = mock_account
    mock_deps["crypto_repo"].find_by_name_or_symbol.return_value = mock_crypto

    # Execution
    result = bot_service.remove_favorite(PlatformType.Telegram, "999", "ethereum")

    # Assertion
    mock_deps["fav_repo"].remove_favorite.assert_not_called()
    assert "is not in your favorites" in result


# Testen für das Auflisten von Favoriten, Fall mit Preisen
@pytest.mark.asyncio
async def test_list_favorites_with_prices(bot_service, mock_deps):
    # Setup
    mock_crypto = Cryptocurrency(symbol="BTC", full_name="Bitcoin")
    mock_account = Account(favorite_cryptos=[mock_crypto])

    mock_deps["account_repo"].find_by_platform_and_id.return_value = mock_account
    mock_deps["api_service"].get_index.return_value = 50000.00

    # Execution
    result = await bot_service.list_favorites(PlatformType.Discord, "123")

    # Assertion
    assert "Bitcoin" in result
    assert "BTC" in result
    assert "50000.00 €" in result


# Testen für das Auflisten von Favoriten, Fall keine Favoriten
@pytest.mark.asyncio
async def test_list_favorites_empty(bot_service, mock_deps):
    # Setup
    mock_account = Account(favorite_cryptos=[])
    mock_deps["account_repo"].find_by_platform_and_id.return_value = mock_account

    # Execution
    result = await bot_service.list_favorites(PlatformType.Discord, "123")

    # Assertion
    assert "no favorite cryptocurrencies" in result


# Testen für das Löschen aller Favoriten, Fall success
def test_drop_favorites_success(bot_service, mock_deps):
    # Setup
    mock_crypto = Cryptocurrency(symbol="BTC", full_name="Bitcoin")
    mock_account = Account(favorite_cryptos=[mock_crypto])
    mock_deps["account_repo"].find_by_platform_and_id.return_value = mock_account

    # Execution
    result = bot_service.drop_favorites(PlatformType.Telegram, "555")

    # Assertion
    mock_deps["fav_repo"].drop_favorites.assert_called_once()
    assert "All favorite cryptocurrencies have been removed" in result
