from app.bots.constants.commands import COMMAND_EXAMPLES


def get_currency_display(vs_currency_symbol: str) -> str:
    """
    Get the currency symbol or short name for display.
    Returns € for EUR, $ for USD, or the currency short name in uppercase for others.
    """
    vs_currency_upper = vs_currency_symbol.upper()
    if vs_currency_upper == "EUR":
        return "€"
    elif vs_currency_upper == "USD":
        return "$"
    else:
        return vs_currency_upper


def get_command_example(command_name: str) -> str:
    """Generate command-specific usage examples based on the command name."""
    if command_name and command_name in COMMAND_EXAMPLES:
        return f"\nUsage example: {COMMAND_EXAMPLES[command_name]}"
    return ""
