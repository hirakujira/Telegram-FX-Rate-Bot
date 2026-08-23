import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

if "telebot" not in sys.modules:
    telebot_stub = ModuleType("telebot")
    telebot_stub.TeleBot = None
    sys.modules["telebot"] = telebot_stub

from crypto_api import UnknownCryptoSymbol
from fx_api import FXRateNotFound
from main import RATE_ERROR_MESSAGE, UNKNOWN_CURRENCY_MESSAGE, create_bot


class FakeBot:
    def __init__(self, _token):
        self.handler = None
        self.replies = []

    def message_handler(self, commands):
        def register(handler):
            self.handler = handler
            return handler

        return register

    def reply_to(self, _message, text, **_kwargs):
        self.replies.append(text)


class FakeFXClient:
    def __init__(self):
        self.get_exchange_rate_called = False

    def get_currency_list(self):
        return ["USD", "TWD"]

    def get_exchange_rate(self, *_args):
        self.get_exchange_rate_called = True
        return {"result": 30, "timestamp": 0}


class FailingCryptoClient:
    def get_exchange_rate(self, *_args):
        return None


class UnknownCryptoClient:
    def get_exchange_rate(self, *_args):
        raise UnknownCryptoSymbol("FLOKI")


class UnknownFXClient(FakeFXClient):
    def get_exchange_rate(self, *_args):
        raise FXRateNotFound


class CurrencyConversionHandlerTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(bot_token="token", channels=[])
        self.message = SimpleNamespace(text="/cur FLOKI USD", chat=SimpleNamespace(id=1))

    def create_bot(self, crypto_client, fx_client=None):
        with patch("main.telebot.TeleBot", FakeBot):
            return create_bot(self.config, fx_client or UnknownFXClient(), crypto_client)

    def test_reports_rate_error_when_known_crypto_quote_fails(self):
        bot = self.create_bot(FailingCryptoClient())

        bot.handler(self.message)

        self.assertEqual(bot.replies, [RATE_ERROR_MESSAGE])

    def test_reports_unknown_error_when_crypto_symbol_is_not_found(self):
        bot = self.create_bot(UnknownCryptoClient())

        bot.handler(self.message)

        self.assertEqual(bot.replies, [UNKNOWN_CURRENCY_MESSAGE.format("FLOKI")])


if __name__ == "__main__":
    unittest.main()
