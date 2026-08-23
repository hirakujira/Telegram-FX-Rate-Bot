import logging

import telebot

from config import load_config
from crypto_api import CryptoPriceClient, UnknownCryptoSymbol
from formatter import format_conversion_message
from fx_api import FXRateClient, FXRateNotFound
from parser import parse_currency_input

FORMAT_ERROR_MESSAGE = "格式錯誤。請使用 /cur <金額> <從幣種> <到幣種>"
RATE_ERROR_MESSAGE = "無法取得匯率資料。"
UNAUTHORIZED_MESSAGE = "您沒有權限使用此指令。"
UNKNOWN_CURRENCY_MESSAGE = "找不到幣種: {}"


def create_bot(config, fx_client=None, crypto_client=None):
    bot = telebot.TeleBot(config.bot_token)
    fx_client = fx_client or FXRateClient()
    crypto_client = crypto_client or CryptoPriceClient(
        api_key=getattr(config, "coingecko_api_key", None)
    )

    @bot.message_handler(commands=["cur"])
    def handle_currency_conversion(message):
        try:
            if config.channels and message.chat.id not in config.channels:
                bot.reply_to(message, UNAUTHORIZED_MESSAGE)
                return

            parsed_input = parse_currency_input(
                message.text.replace("/cur ", "").replace("=", "").replace(",", ""),
                (),
                validate_currencies=False,
            )
            if not parsed_input:
                bot.reply_to(message, FORMAT_ERROR_MESSAGE)
                return

            try:
                data = fx_client.get_exchange_rate(
                    parsed_input.amount,
                    parsed_input.from_currency,
                    parsed_input.to_currency,
                )
            except FXRateNotFound:
                try:
                    data = crypto_client.get_exchange_rate(
                        parsed_input.amount,
                        parsed_input.from_currency,
                        parsed_input.to_currency,
                    )
                except UnknownCryptoSymbol as error:
                    bot.reply_to(
                        message, UNKNOWN_CURRENCY_MESSAGE.format(error.symbol)
                    )
                    return
            if data is None:
                bot.reply_to(message, RATE_ERROR_MESSAGE)
                return

            bot.reply_to(
                message,
                format_conversion_message(
                    parsed_input.amount,
                    parsed_input.from_currency,
                    parsed_input.to_currency,
                    data["result"],
                    data["timestamp"],
                ),
                parse_mode="Markdown",
            )
        except Exception:
            logging.exception("Failed to process currency conversion")
            bot.reply_to(message, FORMAT_ERROR_MESSAGE)

    return bot


def main():
    config = load_config()
    create_bot(config).polling()


if __name__ == "__main__":
    main()
