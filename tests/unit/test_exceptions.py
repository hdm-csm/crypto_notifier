# Passe den Import-Pfad an, falls deine Exceptions in einer anderen Datei liegen
from app.utils.exceptions import (
    AccountNotFoundOrCreatedException,
    InvokeSetupError,
    MissingCommandArguments,
    InvalidNotificationArguments,
)


class TestAccountNotFoundOrCreatedException:
    """Tests für AccountNotFoundOrCreatedException"""

    def test_exception_formatting(self):
        # Arrange
        original = "Database connection timed out"
        custom = "Failed to create user profile"

        # Act
        exc = AccountNotFoundOrCreatedException(original_message=original, custom_message=custom)

        # Assert
        expected_message = f"{custom}:\n {original}"
        assert exc.message == expected_message
        assert str(exc) == expected_message


class TestInvokeSetupError:
    """Tests für InvokeSetupError"""

    def test_exception_string_representation(self):
        # Act
        exc = InvokeSetupError()

        # Assert
        assert str(exc) == "Database setup failed"


class TestMissingCommandArguments:
    """Tests für MissingCommandArguments"""

    def test_exception_without_missing_args(self):
        # Act
        exc = MissingCommandArguments(command_name="price")

        # Assert
        assert exc.command_name == "price"
        assert exc.missing_args == ""
        assert str(exc) == "Missing required arguments for /price"

    def test_exception_with_missing_args(self):
        # Act
        exc = MissingCommandArguments(command_name="set_vs", missing_args="<currency>")

        # Assert
        assert exc.command_name == "set_vs"
        assert exc.missing_args == "<currency>"
        assert str(exc) == "Missing required arguments for /set_vs: <currency>"


class TestInvalidNotificationArguments:
    """Tests für InvalidNotificationArguments"""

    def test_exception_with_all_arguments(self):
        # Act
        exc = InvalidNotificationArguments(
            message="Invalid target price", usage_hint="Use /add_notif <price>"
        )

        # Assert
        assert exc.usage_hint == "Use /add_notif <price>"
        assert str(exc) == "Invalid target price"

    def test_exception_with_default_arguments(self):
        # Act
        exc = InvalidNotificationArguments()

        # Assert
        assert exc.usage_hint == ""
        assert str(exc) == ""
