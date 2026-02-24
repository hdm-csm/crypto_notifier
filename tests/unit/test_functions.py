import pytest
from unittest.mock import patch
from app.models.dtos import CryptoPrice

# Passe den Import-Pfad an, falls deine Datei anderswo liegt
from app.utils.functions import (
    get_currency_display,
    get_command_example,
    format_price_info,
    format_price_infos,
)


class TestGetCurrencyDisplay:
    """Tests für get_currency_display"""

    @pytest.mark.parametrize(
        "input_symbol, expected",
        [
            ("EUR", "€"),
            ("eur", "€"),
            ("USD", "$"),
            ("usd", "$"),
            ("GBP", "GBP"),
            ("jpy", "JPY"),
            ("", ""),
        ],
    )
    def test_get_currency_display(self, input_symbol, expected):
        # Act
        result = get_currency_display(input_symbol)

        # Assert
        assert result == expected


class TestGetCommandExample:
    """Tests für get_command_example"""

    @patch.dict("app.utils.functions.COMMAND_EXAMPLES", {"add": "/add <crypto>"})
    def test_get_command_example_known_command(self):
        # Act
        result = get_command_example("add")

        # Assert
        assert result == "\nUsage example: /add <crypto>"

    @patch.dict("app.utils.functions.COMMAND_EXAMPLES", {"add": "/add <crypto>"})
    def test_get_command_example_unknown_command(self):
        # Act
        result = get_command_example("remove")

        # Assert
        assert result == ""

    def test_get_command_example_empty_input(self):
        # Act
        result = get_command_example("")

        # Assert
        assert result == ""


class TestFormatPriceInfo:
    """Tests für format_price_info"""

    def test_format_price_info_error(self):
        # Arrange
        price_info = CryptoPrice(price=0.0, error=True, only_usd=False, self_converted=False)

        # Act
        result = format_price_info("btc", "usd", price_info)

        # Assert
        assert result == "• BTC/USD: ❌ Unavailable"

    def test_format_price_info_zero_price(self):
        # Arrange
        price_info = CryptoPrice(price=0.0, error=False, only_usd=False, self_converted=False)

        # Act
        result = format_price_info("btc", "eur", price_info)

        # Assert: Kein Leerzeichen nach €
        assert result == "• BTC/EUR: €0.00"

    @pytest.mark.parametrize(
        "price, expected_str",
        [
            (1.0, "1.00"),
            (1234.5678, "1,234.57"),  # Auf 2 Dezimalstellen gerundet mit Tausendertrennzeichen
            (50000.0, "50,000.00"),
        ],
    )
    def test_format_price_info_large_prices(self, price, expected_str):
        # Arrange
        price_info = CryptoPrice(price=price, error=False, only_usd=False, self_converted=False)

        # Act
        result = format_price_info("eth", "usd", price_info)

        # Assert: Kein Leerzeichen nach $
        assert result == f"• ETH/USD: ${expected_str}"

    @pytest.mark.parametrize(
        "price, expected_str",
        [
            (0.5, "0.5"),
            (0.1234567, "0.123457"),  # Auf 6 Dezimalstellen gerundet
            (0.0001, "0.0001"),
            (0.999999, "0.999999"),
        ],
    )
    def test_format_price_info_small_prices(self, price, expected_str):
        # Arrange
        price_info = CryptoPrice(price=price, error=False, only_usd=False, self_converted=False)

        # Act
        result = format_price_info("shib", "eur", price_info)

        # Assert: Kein Leerzeichen nach €
        assert result == f"• SHIB/EUR: €{expected_str}"

    def test_format_price_info_only_usd_fallback(self):
        # Arrange
        price_info = CryptoPrice(price=50000.0, error=False, only_usd=True, self_converted=False)

        # Act
        result = format_price_info("btc", "eur", price_info)

        # Assert: USD Zeichen muss benutzt werden, da Fallback greift. Kein Leerzeichen.
        assert result == "• BTC/EUR: $50,000.00 (Fallback)"

    def test_format_price_info_self_converted(self):
        # Arrange
        price_info = CryptoPrice(price=45000.0, error=False, only_usd=False, self_converted=True)

        # Act
        result = format_price_info("btc", "gbp", price_info)

        # Assert: GBP hat 3 Zeichen, daher WIRD ein Leerzeichen eingefügt laut Code!
        assert result == "• BTC/GBP: ≈ GBP 45,000.00 (Self-Converted)"


class TestFormatPriceInfos:
    """Tests für format_price_infos"""

    def test_format_price_infos_empty_list(self):
        # Act
        result = format_price_infos([])

        # Assert
        assert result == "ℹ️ No price data available for favorites."

    def test_format_price_infos_multiple_items(self):
        # Arrange
        price_1 = CryptoPrice(price=50000.0, error=False, only_usd=False, self_converted=False)
        price_2 = CryptoPrice(price=0.0, error=True, only_usd=False, self_converted=False)

        ticker_results = [
            ("btc", "usd", price_1),
            ("eth", "usd", price_2),
        ]

        # Act
        result = format_price_infos(ticker_results)

        # Assert: Kein Leerzeichen nach $
        expected_lines = ["• BTC/USD: $50,000.00", "• ETH/USD: ❌ Unavailable"]
        assert result == "\n".join(expected_lines)
