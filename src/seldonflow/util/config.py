from pathlib import Path
from enum import Enum
import yaml

CONFIG_PATH = Path("config")
API_KEYS_FILENAME = "api_keys.yaml"


class ConfigType(Enum):
    Invalid = 0
    API_KEYS = 1


class Config:
    def __init__(self, types: list[ConfigType] = [ConfigType.API_KEYS]):
        self._types = types
        self._configs = {}
        self.load_configs()

    def load_configs(self):
        for config_type in self._types:
            self.load_config(config_type)

    def load_config(self, config_type: ConfigType):
        if config_type == ConfigType.API_KEYS:
            self.load_api_keys()
        else:
            return

    def load_api_keys(self, config_file_path=CONFIG_PATH / API_KEYS_FILENAME):
        with open(config_file_path, "r") as file:
            self._configs[ConfigType.API_KEYS] = yaml.safe_load(file)

    def api_keys(self):
        return self._configs.get(ConfigType.API_KEYS, {})


def main():
    print(f"{CONFIG_PATH / API_KEYS_FILENAME}")
    config = Config()
    config.load_configs()
    print(f"{config._configs}")
    print(f"{config.api_keys()}")
    print(f"{config._types}")


if __name__ == "__main__":
    main()
