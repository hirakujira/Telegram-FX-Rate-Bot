import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fx_api import FXRateClient, FXRateNotFound


class FXRateClientTests(unittest.TestCase):
    def test_reports_missing_numeric_result_for_crypto_fallback(self):
        response = Mock()
        response.json.return_value = {"result": None, "timestamp": 123}
        session = Mock()
        session.get.return_value = response

        with self.assertRaises(FXRateNotFound):
            FXRateClient(session).get_exchange_rate(1, "USDT", "USD")

    def test_reports_unsupported_fx_pair_for_crypto_fallback(self):
        response = Mock(status_code=400)
        session = Mock()
        session.get.return_value.raise_for_status.side_effect = requests.HTTPError(
            response=response
        )

        with self.assertRaises(FXRateNotFound):
            FXRateClient(session).get_exchange_rate(1, "DOGE", "USD")


if __name__ == "__main__":
    unittest.main()
