import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from crypto_api import (
    CryptoPriceClient,
    SEARCH_URL,
    SIMPLE_PRICE_URL,
    UnknownCryptoSymbol,
)
from parser import CurrencyConversion, parse_currency_input


def response(data):
    mock_response = Mock()
    mock_response.json.return_value = data
    return mock_response


class CryptoPriceClientTests(unittest.TestCase):
    def test_selects_exact_symbol_with_lowest_market_cap_rank(self):
        session = Mock()
        session.get.side_effect = [
            response(
                {
                    "coins": [
                        {"id": "not-bitcoin", "symbol": "bitcoin", "market_cap_rank": 1},
                        {"id": "bitcoin-test", "symbol": "btc", "market_cap_rank": 99},
                        {"id": "bitcoin", "symbol": "BTC", "market_cap_rank": 1},
                    ]
                }
            ),
            response({"bitcoin": {"usd": 100000}}),
        ]

        with patch("crypto_api.time.time", return_value=123):
            result = CryptoPriceClient(session).get_exchange_rate(
                2, "BTC", "USD"
            )

        self.assertEqual(result, {"result": 200000, "timestamp": 123})
        self.assertEqual(session.get.call_args_list[0].args[0], SEARCH_URL)
        self.assertEqual(
            session.get.call_args_list[1],
            unittest.mock.call(
                SIMPLE_PRICE_URL,
                params={"ids": "bitcoin", "vs_currencies": "usd"},
                timeout=10,
                headers=None,
            ),
        )

    def test_converts_crypto_to_fiat(self):
        session = Mock()
        session.get.side_effect = [
            response({"coins": [{"id": "bitcoin", "symbol": "btc", "market_cap_rank": 1}]}),
            response({"bitcoin": {"usd": 50000}}),
        ]

        result = CryptoPriceClient(session).get_exchange_rate(2, "BTC", "USD")

        self.assertEqual(result["result"], 100000)

    def test_converts_stablecoin_using_requested_quote_currency(self):
        session = Mock()
        session.get.side_effect = [
            response({"coins": [{"id": "tether", "symbol": "usdt", "market_cap_rank": 3}]}),
            response({"tether": {"usd": 1}}),
        ]

        result = CryptoPriceClient(session).get_exchange_rate(1, "USDT", "USD")

        self.assertEqual(result["result"], 1)

    def test_uses_requested_quote_currency(self):
        session = Mock()
        session.get.side_effect = [
            response(
                {"coins": [{"id": "bitcoin", "symbol": "btc", "market_cap_rank": 1}]}
            ),
            response({"bitcoin": {"eth": 40}}),
        ]

        result = CryptoPriceClient(session).get_exchange_rate(1, "BTC", "ETH")

        self.assertEqual(result["result"], 40)

    def test_converts_to_crypto_when_direct_quote_is_unavailable(self):
        session = Mock()
        session.get.side_effect = [
            response({"coins": [{"id": "solana", "symbol": "sol", "market_cap_rank": 6}]}),
            response({"solana": {}}),
            response({"coins": [{"id": "tether", "symbol": "usdt", "market_cap_rank": 3}]}),
            response({"solana": {"usd": 200}, "tether": {"usd": 1}}),
        ]

        result = CryptoPriceClient(session).get_exchange_rate(1, "SOL", "USDT")

        self.assertEqual(result["result"], 200)
        self.assertEqual(
            session.get.call_args_list[3].kwargs["params"],
            {"ids": "solana,tether", "vs_currencies": "usd"},
        )

    def test_uses_id_to_break_ties_for_missing_market_cap_rank(self):
        session = Mock()
        session.get.side_effect = [
            response(
                {
                    "coins": [
                        {"id": "z-coin", "symbol": "btc", "market_cap_rank": None},
                        {"id": "a-coin", "symbol": "BTC"},
                    ]
                }
            ),
            response({"a-coin": {"usd": 1}}),
        ]

        result = CryptoPriceClient(session).get_exchange_rate(1, "BTC", "USD")

        self.assertEqual(result["result"], 1)
        self.assertEqual(session.get.call_args_list[1].kwargs["params"]["ids"], "a-coin")

    def test_returns_none_when_price_response_is_invalid(self):
        session = Mock()
        session.get.side_effect = [
            response({"coins": [{"id": "bitcoin", "symbol": "btc", "market_cap_rank": 1}]}),
            response({"bitcoin": {}}),
            response({"coins": []}),
        ]

        self.assertIsNone(
            CryptoPriceClient(session).get_exchange_rate(1, "BTC", "USD")
        )

    def test_reports_unknown_crypto_symbol(self):
        session = Mock()
        session.get.return_value = response({"coins": []})

        with self.assertRaisesRegex(UnknownCryptoSymbol, "FLOKI"):
            CryptoPriceClient(session).get_exchange_rate(1, "FLOKI", "USD")

    def test_uses_demo_api_key_when_configured(self):
        session = Mock()
        session.get.side_effect = [
            response({"coins": [{"id": "bitcoin", "symbol": "btc", "market_cap_rank": 1}]}),
            response({"bitcoin": {"usd": 1}}),
        ]

        CryptoPriceClient(session, api_key="test-key").get_exchange_rate(
            1, "BTC", "USD"
        )

        self.assertEqual(
            session.get.call_args_list[0].kwargs["headers"],
            {"x-cg-demo-api-key": "test-key"},
        )


class ParseCurrencyInputValidationTests(unittest.TestCase):
    def test_can_skip_currency_validation_for_crypto_routing(self):
        self.assertEqual(
            parse_currency_input("BTC USD", ["USD"], validate_currencies=False),
            CurrencyConversion(1, "BTC", "USD"),
        )

    def test_parses_five_character_crypto_symbol(self):
        self.assertEqual(
            parse_currency_input("FLOKI USD", ["USD"], validate_currencies=False),
            CurrencyConversion(1, "FLOKI", "USD"),
        )


if __name__ == "__main__":
    unittest.main()
