import pytest
from unittest.mock import Mock, MagicMock

from app.services.account_lookup_service import AccountLookupService
from app.models.enums import PlatformType
from app.models.schemas import Account, VsCurrency
from app.utils.exceptions import AccountNotFoundOrCreatedException


@pytest.fixture
def mock_account_repo():
    return Mock()


@pytest.fixture
def mock_vs_currency_repo():
    return Mock()


@pytest.fixture
def mock_session():
    # Simuliert die SQLAlchemy Session
    return MagicMock()


@pytest.fixture
def account_lookup_service(mock_account_repo, mock_vs_currency_repo):
    # Initialisiert den Service mit gemockten Repositories
    return AccountLookupService(
        account_repository=mock_account_repo, vs_currency_repository=mock_vs_currency_repo
    )


class TestFindOrCreateAccount:
    """Tests für find_or_create_account"""

    def test_returns_existing_account(
        self, account_lookup_service, mock_account_repo, mock_vs_currency_repo, mock_session
    ):
        # Arrange: Simuliere ein bereits existierendes Konto
        existing_account = Account(id=1, platform_user_id="12345")
        mock_account_repo.find_by_platform_and_id.return_value = existing_account

        # Act
        result = account_lookup_service.find_or_create_account(
            db_session=mock_session, platform_type=PlatformType.DISCORD, platform_user_id="12345"
        )

        # Assert: Prüfe, ob das existierende Konto zurückgegeben wurde
        assert result == existing_account

        # Verify: Erstellungsmethoden dürfen nicht aufgerufen worden sein
        mock_vs_currency_repo.find_by_short_name.assert_not_called()
        mock_account_repo.create.assert_not_called()

    def test_creates_new_account_with_eur_currency(
        self, account_lookup_service, mock_account_repo, mock_vs_currency_repo, mock_session
    ):
        # Arrange: Simuliere, dass das Konto nicht existiert, aber EUR vorhanden ist
        mock_account_repo.find_by_platform_and_id.return_value = None

        eur_currency = VsCurrency(id=99, symbol="EUR")
        mock_vs_currency_repo.find_by_short_name.return_value = eur_currency

        new_account = Account(id=2, platform_user_id="67890")
        mock_account_repo.create.return_value = new_account

        # Act
        result = account_lookup_service.find_or_create_account(
            db_session=mock_session, platform_type=PlatformType.TELEGRAM, platform_user_id="67890"
        )

        # Assert: Prüfe, ob das neue Konto zurückgegeben wurde
        assert result == new_account

        # Verify: Prüfe, ob create mit der korrekten EUR-ID (99) aufgerufen wurde
        mock_account_repo.create.assert_called_once_with(
            session=mock_session,
            platform=PlatformType.TELEGRAM,
            platform_user_id="67890",
            selected_vs_currency_id=99,
        )

    def test_creates_new_account_without_eur_fallback(
        self, account_lookup_service, mock_account_repo, mock_vs_currency_repo, mock_session
    ):
        # Arrange: Simuliere, dass weder das Konto noch die EUR-Währung existieren
        mock_account_repo.find_by_platform_and_id.return_value = None
        mock_vs_currency_repo.find_by_short_name.return_value = None

        new_account = Account(id=3, platform_user_id="abcde")
        mock_account_repo.create.return_value = new_account

        # Act
        result = account_lookup_service.find_or_create_account(
            db_session=mock_session, platform_type=PlatformType.DISCORD, platform_user_id="abcde"
        )

        # Assert
        assert result == new_account

        # Verify: Prüfe, ob create mit der Fallback-ID (0) aufgerufen wurde
        mock_account_repo.create.assert_called_once_with(
            session=mock_session,
            platform=PlatformType.DISCORD,
            platform_user_id="abcde",
            selected_vs_currency_id=0,
        )

    def test_raises_exception_on_database_error(
        self, account_lookup_service, mock_account_repo, mock_session
    ):
        # Arrange: Erzwinge einen Fehler bei der Datenbankabfrage
        mock_account_repo.find_by_platform_and_id.side_effect = Exception("Simulierter DB Fehler")

        # Act & Assert: Prüfe, ob die Exception gefangen und neu geworfen wird
        with pytest.raises(AccountNotFoundOrCreatedException) as exc:
            account_lookup_service.find_or_create_account(
                db_session=mock_session,
                platform_type=PlatformType.DISCORD,
                platform_user_id="error_user",
            )

        # Verify: Prüfe die korrekte Fehlermeldung
        error_text = str(exc.value)
        assert "Could not find or create account" in error_text
        assert "error_user" in error_text
