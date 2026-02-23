from app.bots.constants.commands import COMMAND_EXAMPLES
from app.models.dtos import CryptoPrice
from app.models.typealiases import CryptoSymbolStr, VsCurrencySymbolStr


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


def format_price_info(crypto_symbol: str, vs_currency_symbol: str, price_info: CryptoPrice) -> str:
    """Formats a single ticker result into a readable string."""
    c, v = crypto_symbol.upper(), vs_currency_symbol.upper()
    line: str = ""
    if price_info.error:
        line = f"• {c}/{v}: ❌ Unavailable"
        return line
    p = price_info.price
    if p == 0.0:
        price_str = "0.00"
    elif p >= 1.0:
        price_str = f"{p:,.2f}"
    else:
        price_str = f"{p:,.6f}".rstrip("0").rstrip(".")
    vs_display = get_currency_display(v)
    vs_prefix = f"{vs_display} " if len(vs_display) > 1 else vs_display
    if price_info.only_usd:
        usd_prefix = get_currency_display("USD")
        line = f"• {c}/{v}: {usd_prefix}{price_str} (Fallback)"
    elif price_info.self_converted:
        line = f"• {c}/{v}: ≈ {vs_prefix}{price_str} (Self-Converted)"
    else:
        line = f"• {c}/{v}: {vs_prefix}{price_str}"
    return line


def format_price_infos(
    ticker_results: list[tuple[CryptoSymbolStr, VsCurrencySymbolStr, CryptoPrice]],
) -> str:
    """Formats a list of ticker results into a readable multi-line string."""
    if not ticker_results:
        return "ℹ️ No price data available for favorites."
    lines = []
    for crypto, vs, price_info in ticker_results:
        line = format_price_info(crypto, vs, price_info)
        lines.append(line)
    return "\n".join(lines)
