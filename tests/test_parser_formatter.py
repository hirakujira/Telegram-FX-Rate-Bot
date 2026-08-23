import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from formatter import format_conversion_message
from parser import CurrencyConversion, UnsupportedCurrency, parse_currency_input


class ParseCurrencyInputTests(unittest.TestCase):
    def test_parses_amount_and_target_currency(self):
        self.assertEqual(
            parse_currency_input("1,234.5 usd jpy".replace(",", ""), ["USD", "JPY"]),
            CurrencyConversion(1234.5, "USD", "JPY"),
        )

    def test_uses_default_target_and_reports_unknown_currency(self):
        self.assertEqual(
            parse_currency_input("USD", ["USD", "TWD"]),
            CurrencyConversion(1, "USD", "TWD"),
        )
        self.assertEqual(
            parse_currency_input("USD JPY", ["USD", "TWD"]),
            UnsupportedCurrency("JPY"),
        )


class FormatConversionMessageTests(unittest.TestCase):
    def test_formats_regular_conversion(self):
        timestamp = datetime(2024, 1, 2, 3, 4).timestamp()
        self.assertEqual(
            format_conversion_message(1000, "USD", "TWD", 31500, timestamp),
            "`💰1,000 USD = 31,500 TWD`\n\n更新時間: 2024-01-02 03:04",
        )

    def test_formats_small_conversion(self):
        timestamp = datetime(2024, 1, 2, 3, 4).timestamp()
        self.assertEqual(
            format_conversion_message(1.5, "USD", "JPY", 0.001, timestamp),
            "`💰1.50 USD = < 0.01 JPY`\n\n更新時間: 2024-01-02 03:04",
        )


if __name__ == "__main__":
    unittest.main()
