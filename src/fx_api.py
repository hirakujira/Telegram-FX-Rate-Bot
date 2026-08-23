import logging

import requests

CURRENCIES_URL = "https://api.fxratesapi.com/currencies?format=json"
CONVERT_URL = "https://api.fxratesapi.com/convert"
REQUEST_TIMEOUT_SECONDS = 10


class FXRateClient:
    def __init__(self, session=requests):
        self.session = session

    def get_currency_list(self):
        try:
            response = self.session.get(
                CURRENCIES_URL, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Currencies response is not an object")

            currencies = [
                currency["code"]
                for currency in data.values()
                if isinstance(currency, dict) and isinstance(currency.get("code"), str)
            ]
            if not currencies:
                raise ValueError("Currencies response contains no currency codes")
            return currencies
        except (requests.RequestException, ValueError, TypeError) as error:
            logging.warning("Could not fetch currency list: %s", error)
            return None

    def get_exchange_rate(self, amount, from_currency, to_currency):
        try:
            response = self.session.get(
                CONVERT_URL,
                params={
                    "from": from_currency,
                    "to": to_currency,
                    "amount": amount,
                    "format": "json",
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Conversion response is not an object")
            if "result" not in data or "timestamp" not in data:
                raise ValueError("Conversion response is missing required fields")
            return data
        except (requests.RequestException, ValueError, TypeError) as error:
            logging.warning("Could not fetch exchange rate: %s", error)
            return None
