from seldonflow.strategy.strategy_types import StrategyType
from seldonflow.util.custom_types import Seconds
from seldonflow.util.logger import LoggingMixin
from pathlib import Path
from enum import Enum
import yaml

CONFIG_PATH = Path("config")
API_KEYS_FILENAME = "api_keys.yaml"
STRATEGY_FILENAME = "strategy.yaml"


class ConfigType(Enum):
    Invalid = 0
    Api_Keys = 1
    Strategy = 2


class Config(LoggingMixin):
    def __init__(
        self, types: list[ConfigType] = [ConfigType.Api_Keys, ConfigType.Strategy]
    ):
        super().__init__()
        self._types = types
        self._configs = {}
        self.load_configs()
        self.logger.debug(f"Config Initialized")

    def load_configs(self):
        for config_type in self._types:
            self.load_config(config_type)

    def load_config(self, config_type: ConfigType):
        if config_type == ConfigType.Api_Keys:
            self.load_api_keys()
        if config_type == ConfigType.Strategy:
            self.load_strategies()
        else:
            return

    def load_strategies(self, config_file_path=CONFIG_PATH / STRATEGY_FILENAME):
        return_dict = {}
        with open(config_file_path, "r") as file:
            raw_strategies_configs = yaml.safe_load(file)
            for name, strategy_config in raw_strategies_configs.items():
                strategy_type_raw = strategy_config.get("strategy_type", None)
                assert strategy_type_raw
                tick_interval_raw = strategy_config.get("tick_interval", None)
                assert tick_interval_raw
                return_dict[name] = {
                    "strategy_type": StrategyType.from_string(
                        strategy_type_str=strategy_type_raw
                    ),
                    "desc": strategy_config.get("desc", ""),
                    "tick_interval": Seconds(tick_interval_raw),
                    "live": strategy_config.get("live", False),
                    "parameters": strategy_config.get("parameters", {}),
                }
        self._configs[ConfigType.Strategy] = return_dict

    def load_api_keys(self, config_file_path=CONFIG_PATH / API_KEYS_FILENAME):
        with open(config_file_path, "r") as file:
            self._configs[ConfigType.Api_Keys] = yaml.safe_load(file)

    def api_keys(self):
        return self._configs.get(ConfigType.Api_Keys, {})

    def strategies(self) -> dict:
        return self._configs.get(ConfigType.Strategy, {})

    def get_api_key(self, service: str):
        return self.api_keys().get(service, "{}")


def main():
    print(f"{CONFIG_PATH / API_KEYS_FILENAME}")
    config = Config()
    config.load_configs()
    print(f"{config._configs}")
    print(f"{config.api_keys()}")
    print(f"{config._types}")
    print(f"{config.strategies()}")


if __name__ == "__main__":
    main()
