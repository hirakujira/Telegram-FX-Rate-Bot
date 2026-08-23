import logging
import time

import requests

REQUEST_TIMEOUT_SECONDS = 10
COIN_CACHE_TTL_SECONDS = 3600
SEARCH_URL = "https://api.coingecko.com/api/v3/search"
SIMPLE_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"


class UnknownCryptoSymbol(Exception):
    def __init__(self, symbol):
        super().__init__(symbol)
        self.symbol = symbol


class CryptoAPIError(Exception):
    pass


class CryptoPriceClient:
    def __init__(self, session=requests, api_key=None):
        self.session = session
        self.headers = {"x-cg-demo-api-key": api_key} if api_key else None
        self.coin_cache = {}

    def get_exchange_rate(self, amount, from_currency, to_currency):
        try:
            from_coin = self._find_coin(from_currency)
        except CryptoAPIError:
            return None
        if from_coin is None:
            raise UnknownCryptoSymbol(from_currency)

        prices = self._get_prices([from_coin["id"]], to_currency.lower())
        price = prices[from_coin["id"]] if prices else None
        if price is not None and price > 0:
            return {"result": amount * price, "timestamp": time.time()}

        try:
            to_coin = self._find_coin(to_currency)
        except CryptoAPIError:
            return None
        if to_coin is None:
            return None

        prices = self._get_prices([from_coin["id"], to_coin["id"]], "usd")
        from_price = prices[from_coin["id"]] if prices else None
        to_price = prices[to_coin["id"]] if prices else None
        if (
            from_price is None
            or to_price is None
            or from_price <= 0
            or to_price <= 0
        ):
            logging.warning("CoinGecko returned a non-positive price")
            return None

        return {"result": amount * from_price / to_price, "timestamp": time.time()}

    def _find_coin(self, symbol):
        cached_coin = self.coin_cache.get(symbol)
        if cached_coin and time.monotonic() - cached_coin[0] < COIN_CACHE_TTL_SECONDS:
            return cached_coin[1]

        try:
            response = self.session.get(
                SEARCH_URL,
                params={"query": symbol},
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("CoinGecko search response is not an object")
            coins = data.get("coins", [])
            matches = [
                coin
                for coin in coins
                if isinstance(coin, dict)
                and isinstance(coin.get("id"), str)
                and isinstance(coin.get("symbol"), str)
                and coin["symbol"].lower() == symbol.lower()
            ]
            if not matches:
                return None
            coin = min(
                matches,
                key=lambda coin: (
                    not isinstance(coin.get("market_cap_rank"), (int, float)),
                    coin.get("market_cap_rank")
                    if isinstance(coin.get("market_cap_rank"), (int, float))
                    else float("inf"),
                    coin["id"],
                ),
            )
            self.coin_cache[symbol] = (time.monotonic(), coin)
            return coin
        except (requests.RequestException, ValueError, TypeError, KeyError) as error:
            logging.warning("Could not resolve crypto symbol %s: %s", symbol, error)
            raise CryptoAPIError from error

    def _get_prices(self, coin_ids, quote_currency):
        try:
            response = self.session.get(
                SIMPLE_PRICE_URL,
                params={"ids": ",".join(coin_ids), "vs_currencies": quote_currency},
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("CoinGecko price response is not an object")
            prices = {}
            for coin_id in coin_ids:
                coin_prices = data.get(coin_id)
                if not isinstance(coin_prices, dict):
                    return None
                price = coin_prices.get(quote_currency)
                if not isinstance(price, (int, float)):
                    return None
                prices[coin_id] = price
            return prices
        except (requests.RequestException, ValueError, TypeError, KeyError) as error:
            logging.warning(
                "Could not fetch crypto prices for %s in %s: %s",
                ", ".join(coin_ids),
                quote_currency,
                error,
            )
            return None
