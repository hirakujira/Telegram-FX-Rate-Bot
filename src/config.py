import json
from dataclasses import dataclass


@dataclass(frozen=True)
class FXRateConfig:
    bot_token: str
    channels: list


def load_config(path="config.json"):
    with open(path, encoding="utf-8") as config_file:
        data = json.load(config_file)

    return FXRateConfig(
        bot_token=data["bot_token"],
        channels=data["channels"],
    )
