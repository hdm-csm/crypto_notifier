class AccountNotFoundOrCreatedException(Exception):
    """Exception raised when an account could not be found or created in the system."""

    def __init__(self, original_message: str, custom_message: str):
        self.message = f"{custom_message}:\n {original_message}"
        super().__init__(self.message)


class InvokeSetupError(Exception):
    """Stops command execution without stacktrace"""

    def __str__(self):
        return "Database setup failed"


class MissingCommandArguments(Exception):
    """Exception raised when a command is missing required arguments."""

    def __init__(self, command_name: str, missing_args: str = ""):
        self.command_name = command_name
        self.missing_args = missing_args
        message = f"Missing required arguments for /{command_name}"
        if missing_args:
            message += f": {missing_args}"
        super().__init__(message)
