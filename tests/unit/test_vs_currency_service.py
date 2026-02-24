import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.vs_currency_service import VsCurrencyService
from app.models.schemas import Account, VsCurrency


@pytest.fixture
def mock_vs_currency_repo():
    return Mock()


@pytest.fixture
def mock_account_lookup_service():
    return Mock()


@pytest.fixture
def mock_crypto_api_service():
    return AsyncMock()


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def vs_currency_service(
    mock_vs_currency_repo, mock_account_lookup_service, mock_crypto_api_service
):
    return VsCurrencyService(
        vs_currency_repository=mock_vs_currency_repo,
        account_lookup_service=mock_account_lookup_service,
        crypto_api_service=mock_crypto_api_service,
    )


@pytest.fixture
def sample_vs_currency():
    currency = Mock(spec=VsCurrency)
    currency.id = 1
    currency.symbol = "eur"
    currency.name = "Euro"
    return currency


@pytest.fixture
def sample_account(sample_vs_currency):
    account = Mock(spec=Account)
    account.selected_vs_currency = sample_vs_currency
    return account


class TestInitVsCurrencies:
    """Tests für init_vs_currencies (API basiert)"""

    @pytest.mark.asyncio
    @patch("app.services.vs_currency_service.session_scope")
    async def test_init_skips_when_not_empty(
        self,
        mock_session_scope,
        vs_currency_service,
        mock_vs_currency_repo,
        mock_crypto_api_service,
        mock_session,
    ):
        # Arrange: Setup Session und simuliere gefüllte Datenbank
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_scope.return_value = mock_context

        mock_vs_currency_repo.is_empty.return_value = False

        # Act
        await vs_currency_service.init_vs_currencies()

        # Assert: Verifiziere, dass keine Daten geladen oder gespeichert wurden
        mock_crypto_api_service.get_coingecko_supported_vs_currencies.assert_not_called()
        mock_vs_currency_repo.store_all.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.vs_currency_service.session_scope")
    @patch("app.services.vs_currency_service.get_currency_full_name")
    async def test_init_fetches_and_stores_when_empty(
        self,
        mock_get_full_name,
        mock_session_scope,
        vs_currency_service,
        mock_vs_currency_repo,
        mock_crypto_api_service,
        mock_session,
    ):
        # Arrange: Setup Session und simuliere leere Datenbank
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_scope.return_value = mock_context

        mock_vs_currency_repo.is_empty.return_value = True
        mock_crypto_api_service.get_coingecko_supported_vs_currencies.return_value = ["usd", "eur"]
        mock_get_full_name.side_effect = lambda sym: "US Dollar" if sym == "usd" else "Euro"

        # Act
        await vs_currency_service.init_vs_currencies()

        # Assert: Verifiziere API Aufruf und Speicherung
        mock_crypto_api_service.get_coingecko_supported_vs_currencies.assert_called_once()
        mock_vs_currency_repo.store_all.assert_called_once()

        # Prüfe die übergebenen Objekte
        stored_currencies = mock_vs_currency_repo.store_all.call_args[0][1]
        assert len(stored_currencies) == 2
        assert stored_currencies[0].symbol == "usd"
        assert stored_currencies[0].name == "US Dollar"


class TestInitVsCurrenciesFromStatic:
    """Tests für init_vs_currencies_from_static"""

    @patch("app.services.vs_currency_service.session_scope")
    def test_init_static_skips_when_not_empty(
        self, mock_session_scope, vs_currency_service, mock_vs_currency_repo, mock_session
    ):
        # Arrange
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_scope.return_value = mock_context

        mock_vs_currency_repo.is_empty.return_value = False

        # Act
        vs_currency_service.init_vs_currencies_from_static()

        # Assert
        mock_vs_currency_repo.store_all.assert_not_called()

    @patch("app.services.vs_currency_service.session_scope")
    @patch("app.services.vs_currency_service.VS_CURRENCY_MAPPING", {"usd": "US Dollar"})
    def test_init_static_stores_when_empty(
        self, mock_session_scope, vs_currency_service, mock_vs_currency_repo, mock_session
    ):
        # Arrange
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_scope.return_value = mock_context

        mock_vs_currency_repo.is_empty.return_value = True

        # Act
        vs_currency_service.init_vs_currencies_from_static()

        # Assert
        mock_vs_currency_repo.store_all.assert_called_once()
        stored_currencies = mock_vs_currency_repo.store_all.call_args[0][1]
        assert len(stored_currencies) == 1
        assert stored_currencies[0].symbol == "usd"
        assert stored_currencies[0].name == "US Dollar"


class TestGetVsCurrency:
    """Tests für get_vs_currency"""

    def test_get_vs_currency_formats_correctly(self, vs_currency_service, sample_account):
        # Act
        result = vs_currency_service.get_vs_currency(account=sample_account)

        # Assert
        assert "Currency: EUR — Euro" in result
        assert "Change with `/set_vs <code>`" in result


class TestGetAll:
    """Tests für get_all"""

    def test_get_all_returns_list(
        self, vs_currency_service, mock_vs_currency_repo, mock_session, sample_vs_currency
    ):
        # Arrange
        expected_list = [sample_vs_currency]
        mock_vs_currency_repo.get_all.return_value = expected_list

        # Act
        result = vs_currency_service.get_all(db_session=mock_session)

        # Assert
        mock_vs_currency_repo.get_all.assert_called_once_with(mock_session)
        assert result == expected_list


class TestListSupportedVsCurrencies:
    """Tests für list_supported_vs_currencies"""

    def test_list_formats_correctly(
        self, vs_currency_service, mock_vs_currency_repo, mock_session, sample_vs_currency
    ):
        # Arrange
        mock_vs_currency_repo.get_all.return_value = [sample_vs_currency]

        # Act
        result = vs_currency_service.list_supported_vs_currencies(db_session=mock_session)

        # Assert
        assert "Supported currencies (1)" in result
        assert "EUR — Euro" in result
        assert "Change with `/set_vs <code>`" in result


class TestSetVsCurrency:
    """Tests für set_vs_currency"""

    def test_set_vs_currency_not_found(
        self, vs_currency_service, mock_vs_currency_repo, mock_session, sample_account
    ):
        # Arrange
        mock_vs_currency_repo.find_by_symbol_or_name.return_value = None

        # Act
        result = vs_currency_service.set_vs_currency(
            db_session=mock_session, account=sample_account, input="invalid"
        )

        # Assert
        assert result == "❌ Currency 'invalid' not found."
        mock_vs_currency_repo.set_vs_currency.assert_not_called()

    def test_set_vs_currency_success(
        self,
        vs_currency_service,
        mock_vs_currency_repo,
        mock_session,
        sample_account,
        sample_vs_currency,
    ):
        # Arrange
        mock_vs_currency_repo.find_by_symbol_or_name.return_value = sample_vs_currency

        # Act
        result = vs_currency_service.set_vs_currency(
            db_session=mock_session, account=sample_account, input="eur"
        )

        # Assert
        mock_vs_currency_repo.set_vs_currency.assert_called_once_with(
            session=mock_session, account=sample_account, vs_currency_id=1
        )
        assert result == "✅ Currency set to EUR — Euro."


class TestFindBySymbolOrName:
    """Tests für find_by_symbol_or_name"""

    def test_find_by_symbol_or_name(
        self, vs_currency_service, mock_vs_currency_repo, mock_session, sample_vs_currency
    ):
        # Arrange
        mock_vs_currency_repo.find_by_symbol_or_name.return_value = sample_vs_currency

        # Act
        result = vs_currency_service.find_by_symbol_or_name(session=mock_session, input="eur")

        # Assert
        mock_vs_currency_repo.find_by_symbol_or_name.assert_called_once_with(
            session=mock_session, input="eur"
        )
        assert result == sample_vs_currency
