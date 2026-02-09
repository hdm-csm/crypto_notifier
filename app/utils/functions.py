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
