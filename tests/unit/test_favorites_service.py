import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.favorites_service import FavoritesService
from app.models.schemas import Account, Cryptocurrency, VsCurrency


@pytest.fixture
def mock_favorite_repo():
    return Mock()


@pytest.fixture
def mock_crypto_service():
    return Mock()


@pytest.fixture
def mock_crypto_api():
    return AsyncMock()


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def favorites_service(mock_favorite_repo, mock_crypto_service, mock_crypto_api):
    return FavoritesService(
        favorite_repository=mock_favorite_repo,
        crypto_currency_service=mock_crypto_service,
        crypto_api_service=mock_crypto_api,
    )


@pytest.fixture
def sample_account():
    account = Mock(spec=Account)
    account.favorite_cryptos = []
    account.selected_vs_currency = None
    return account


@pytest.fixture
def sample_crypto():
    crypto = Mock(spec=Cryptocurrency)
    crypto.symbol = "BTC"
    crypto.name = "Bitcoin"
    return crypto


class TestAddFavorite:
    """Tests für add_favorite"""

    def test_add_favorite_crypto_not_found(
        self, favorites_service, mock_crypto_service, mock_session, sample_account
    ):
        # Arrange: Simuliere, dass die Kryptowährung nicht existiert
        mock_crypto_service.find_by_name_or_symbol.return_value = None

        # Act
        result = favorites_service.add_favorite(
            db_session=mock_session, account=sample_account, input_crypto="invalid"
        )

        # Assert: Prüfe korrekte Fehlermeldung
        assert result == "❌ 'invalid' not found."
        mock_crypto_service.find_by_name_or_symbol.assert_called_once_with(mock_session, "invalid")

    def test_add_favorite_already_in_favorites(
        self, favorites_service, mock_crypto_service, mock_session, sample_account, sample_crypto
    ):
        # Arrange: Füge Crypto vorab zu Favoriten hinzu
        mock_crypto_service.find_by_name_or_symbol.return_value = sample_crypto
        sample_account.favorite_cryptos = [sample_crypto]

        # Act
        result = favorites_service.add_favorite(
            db_session=mock_session, account=sample_account, input_crypto="BTC"
        )

        # Assert: Prüfe Warnmeldung
        assert result == "⚠️ BTC is already in your favorites."

    def test_add_favorite_success(
        self,
        favorites_service,
        mock_crypto_service,
        mock_favorite_repo,
        mock_session,
        sample_account,
        sample_crypto,
    ):
        # Arrange: Leere Favoritenliste, Crypto existiert
        mock_crypto_service.find_by_name_or_symbol.return_value = sample_crypto
        sample_account.favorite_cryptos = []

        # Act
        result = favorites_service.add_favorite(
            db_session=mock_session, account=sample_account, input_crypto="BTC"
        )

        # Assert: Prüfe Aufruf im Repo und Erfolgsmeldung
        mock_favorite_repo.add_favorite.assert_called_once_with(
            account=sample_account, crypto=sample_crypto
        )
        assert result == "✅ Added Bitcoin (BTC) to favorites."


class TestRemoveFavorite:
    """Tests für remove_favorite"""

    def test_remove_favorite_crypto_not_found(
        self, favorites_service, mock_crypto_service, mock_session, sample_account
    ):
        # Arrange: Simuliere, dass die Kryptowährung nicht existiert
        mock_crypto_service.find_by_name_or_symbol.return_value = None

        # Act
        result = favorites_service.remove_favorite(
            db_session=mock_session, account=sample_account, input_crypto="invalid"
        )

        # Assert
        assert result == "❌ 'invalid' not found."

    def test_remove_favorite_not_in_favorites(
        self, favorites_service, mock_crypto_service, mock_session, sample_account, sample_crypto
    ):
        # Arrange: Crypto existiert, ist aber nicht in den Favoriten
        mock_crypto_service.find_by_name_or_symbol.return_value = sample_crypto
        sample_account.favorite_cryptos = []

        # Act
        result = favorites_service.remove_favorite(
            db_session=mock_session, account=sample_account, input_crypto="BTC"
        )

        # Assert
        assert result == "⚠️ BTC is not in your favorites."

    def test_remove_favorite_success(
        self,
        favorites_service,
        mock_crypto_service,
        mock_favorite_repo,
        mock_session,
        sample_account,
        sample_crypto,
    ):
        # Arrange: Crypto ist in den Favoriten
        mock_crypto_service.find_by_name_or_symbol.return_value = sample_crypto
        sample_account.favorite_cryptos = [sample_crypto]

        # Act
        result = favorites_service.remove_favorite(
            db_session=mock_session, account=sample_account, input_crypto="BTC"
        )

        # Assert: Prüfe Aufruf im Repo und Erfolgsmeldung
        mock_favorite_repo.remove_favorite.assert_called_once_with(
            account=sample_account, crypto=sample_crypto
        )
        assert result == "✅ Removed Bitcoin (BTC) from favorites."


class TestListFavorites:
    """Tests für list_favorites"""

    @pytest.mark.asyncio
    async def test_list_favorites_empty(self, favorites_service, sample_account):
        # Arrange: Keine Favoriten
        sample_account.favorite_cryptos = []

        # Act
        result = await favorites_service.list_favorites(account=sample_account)

        # Assert
        assert result == "ℹ️ No favorites set yet."

    @pytest.mark.asyncio
    @patch("app.services.favorites_service.format_price_infos")
    async def test_list_favorites_with_data_default_currency(
        self, mock_format, favorites_service, mock_crypto_api, sample_account, sample_crypto
    ):
        # Arrange: Favoriten gesetzt, keine explizite Währung gewählt (Fallback auf EUR)
        sample_account.favorite_cryptos = [sample_crypto]
        sample_account.selected_vs_currency = None

        mock_crypto_api.fetch_ticker_prices.return_value = [("BTC", "eur", 50000.0)]
        mock_format.return_value = "Formatted Prices"

        # Act
        result = await favorites_service.list_favorites(account=sample_account)

        # Assert: Prüfe, ob API mit Fallback EUR aufgerufen wurde
        mock_crypto_api.fetch_ticker_prices.assert_called_once_with(ticker_pairs={("BTC", "EUR")})
        assert "⭐ Favorites" in result
        assert "Formatted Prices" in result

    @pytest.mark.asyncio
    @patch("app.services.favorites_service.format_price_infos")
    async def test_list_favorites_with_custom_currency(
        self, mock_format, favorites_service, mock_crypto_api, sample_account, sample_crypto
    ):
        # Arrange: Favoriten gesetzt, eigene Währung gewählt (USD)
        sample_account.favorite_cryptos = [sample_crypto]
        custom_currency = Mock(spec=VsCurrency)
        custom_currency.symbol = "USD"
        sample_account.selected_vs_currency = custom_currency

        mock_crypto_api.fetch_ticker_prices.return_value = [("BTC", "usd", 55000.0)]
        mock_format.return_value = "Formatted USD Prices"

        # Act
        result = await favorites_service.list_favorites(account=sample_account)

        # Assert: Prüfe, ob API mit der Custom-Währung aufgerufen wurde
        mock_crypto_api.fetch_ticker_prices.assert_called_once_with(ticker_pairs={("BTC", "usd")})
        assert "Formatted USD Prices" in result


class TestDropFavorites:
    """Tests für drop_favorites"""

    def test_drop_favorites_empty(self, favorites_service, sample_account):
        # Arrange: Keine Favoriten vorhanden
        sample_account.favorite_cryptos = []

        # Act
        result = favorites_service.drop_favorites(account=sample_account)

        # Assert
        assert result == "ℹ️ No favorites to remove."

    def test_drop_favorites_success(
        self, favorites_service, mock_favorite_repo, sample_account, sample_crypto
    ):
        # Arrange: Favoriten vorhanden
        sample_account.favorite_cryptos = [sample_crypto]

        # Act
        result = favorites_service.drop_favorites(account=sample_account)

        # Assert: Prüfe Repo-Aufruf und Meldung
        mock_favorite_repo.drop_favorites.assert_called_once_with(account=sample_account)
        assert result == "✅ All favorites removed."
