import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.services.crypto_currency_service import CryptoCurrencyService
from app.models.schemas import Cryptocurrency


@pytest.fixture
def mock_crypto_repo():
    return Mock()


@pytest.fixture
def mock_crypto_api():
    return AsyncMock()


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def crypto_service(mock_crypto_repo, mock_crypto_api):
    return CryptoCurrencyService(
        crypto_currency_repository=mock_crypto_repo, crypto_api_service=mock_crypto_api
    )


class TestInitCryptoCurrencies:

    @pytest.mark.asyncio
    @patch("app.services.crypto_currency_service.session_scope")
    async def test_init_skips_when_not_empty(
        self, mock_session_scope, crypto_service, mock_crypto_repo, mock_crypto_api, mock_session
    ):
        # Setup session
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_scope.return_value = mock_context

        mock_crypto_repo.is_empty.return_value = False

        # Execute
        await crypto_service.init_crypto_currencies()

        mock_crypto_api.get_yfinance_supported_crypto_currencies.assert_not_called()
        mock_crypto_repo.store_all.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.crypto_currency_service.session_scope")
    async def test_init_fetches_and_deduplicates_when_empty(
        self, mock_session_scope, crypto_service, mock_crypto_repo, mock_crypto_api, mock_session
    ):
        # Setup session context manager
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_scope.return_value = mock_context

        # Set DB to empty
        mock_crypto_repo.is_empty.return_value = True

        # Create mock coins with duplicates
        coin1 = MagicMock(symbol="BTC")
        coin2 = MagicMock(symbol="ETH")
        coin3 = MagicMock(symbol="BTC")  # Duplicate
        mock_crypto_api.get_yfinance_supported_crypto_currencies.return_value = [
            coin1,
            coin2,
            coin3,
        ]

        # Execute
        await crypto_service.init_crypto_currencies(amount=3)

        # Verify API call
        mock_crypto_api.get_yfinance_supported_crypto_currencies.assert_called_once_with(3)

        # Verify deduplication (only coin1 and coin2 should be stored)
        mock_crypto_repo.store_all.assert_called_once_with(mock_session, [coin1, coin2])


class TestFindByNameOrSymbol:

    def test_find_by_name_or_symbol(self, crypto_service, mock_crypto_repo, mock_session):
        # Setup mock return
        expected_crypto = Cryptocurrency()
        mock_crypto_repo.find_by_name_or_symbol.return_value = expected_crypto

        # Execute
        result = crypto_service.find_by_name_or_symbol(mock_session, "BTC")

        # Verify
        mock_crypto_repo.find_by_name_or_symbol.assert_called_once_with(mock_session, "BTC")
        assert result == expected_crypto


class TestGetAll:

    def test_get_all(self, crypto_service, mock_crypto_repo, mock_session):
        # Setup mock return
        expected_list = [Cryptocurrency(), Cryptocurrency()]
        mock_crypto_repo.get_all.return_value = expected_list

        # Execute
        result = crypto_service.get_all(mock_session)

        # Verify
        mock_crypto_repo.get_all.assert_called_once_with(mock_session)
        assert result == expected_list


class TestGetList:

    def test_get_list_empty(self, crypto_service, mock_crypto_repo, mock_session):
        # Setup empty DB return
        mock_crypto_repo.get_all.return_value = []

        # Execute
        result = crypto_service.get_list(mock_session)

        # Verify error message
        assert "❌ No cryptocurrencies available" in result

    def test_get_list_with_data(self, crypto_service, mock_crypto_repo, mock_session):
        # Setup DB return with coins
        coin1 = Cryptocurrency()
        coin1.name = "Bitcoin"
        coin1.symbol = "BTC"

        coin2 = Cryptocurrency()
        coin2.name = "Ethereum"
        coin2.symbol = "ETH"

        mock_crypto_repo.get_all.return_value = [coin1, coin2]

        # Execute
        result = crypto_service.get_list(mock_session)

        # Verify formatted message
        assert "Supported cryptocurrencies (2)" in result
        assert "Bitcoin (BTC)" in result
        assert "Ethereum (ETH)" in result
