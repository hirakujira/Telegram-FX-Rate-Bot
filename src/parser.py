import re
from dataclasses import dataclass
from typing import Collection, Optional, Union

INPUT_PATTERN = re.compile(
    r"^(\d+(\.\d+)?\s*)?(?:([A-Z0-9]{1,20}))"
    r"(\s+(?:[A-Z0-9]{1,20}))?$"
)
DEFAULT_TO_CURRENCY = "TWD"


@dataclass(frozen=True)
class CurrencyConversion:
    amount: float
    from_currency: str
    to_currency: str


@dataclass(frozen=True)
class UnsupportedCurrency:
    currency: str


def parse_currency_input(
    text: str, supported_currencies: Collection[str], validate_currencies: bool = True
) -> Optional[Union[CurrencyConversion, UnsupportedCurrency]]:
    match = INPUT_PATTERN.match(text.strip().upper())
    if not match:
        return None

    amount, from_currency, to_currency = (
        match.group(1),
        match.group(3),
        match.group(4),
    )
    if validate_currencies and from_currency not in supported_currencies:
        return UnsupportedCurrency(from_currency)
    if (
        validate_currencies
        and to_currency
        and to_currency.strip() not in supported_currencies
    ):
        return UnsupportedCurrency(to_currency.strip())

    return CurrencyConversion(
        amount=float(amount.strip()) if amount else 1,
        from_currency=from_currency,
        to_currency=to_currency.strip() if to_currency else DEFAULT_TO_CURRENCY,
    )
