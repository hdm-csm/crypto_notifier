from app.utils.command_constants import COMMAND_EXAMPLES


def get_currency_display(vs_currency: str) -> str:
    """
    Get the currency symbol or short name for display.
    Returns € for EUR, $ for USD, or the currency short name in uppercase for others.
    """
    vs_currency_lower = vs_currency.lower()
    if vs_currency_lower == "eur":
        return "€"
    elif vs_currency_lower == "usd":
        return "$"
    else:
        return vs_currency.upper()


def get_command_example(command_name: str) -> str:
    """Generate command-specific usage examples based on the command name."""
    if command_name and command_name in COMMAND_EXAMPLES:
        return f"\nUsage example: {COMMAND_EXAMPLES[command_name]}"
    return ""
