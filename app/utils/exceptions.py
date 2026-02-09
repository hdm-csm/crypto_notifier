class AccountNotFoundOrCreatedException(Exception):
    """Exception raised when an account could not be found or created in the system."""

    def __init__(self, original_message: str, custom_message: str):
        self.message = f"{custom_message}:\n {original_message}"
        super().__init__(self.message)


class InvokeSetupError(Exception):
    """Stops command execution without stacktrace"""

    def __str__(self):
        return "Database setup failed"
