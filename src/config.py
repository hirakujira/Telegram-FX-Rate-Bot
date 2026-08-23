import json
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FXRateConfig:
    bot_token: str
    channels: list
    coingecko_api_key: Optional[str] = None


def load_config(path="config.json"):
    with open(path, encoding="utf-8") as config_file:
        data = json.load(config_file)

    return FXRateConfig(
        bot_token=data["bot_token"],
        channels=data["channels"],
        coingecko_api_key=data.get("coingecko_api_key"),
    )
