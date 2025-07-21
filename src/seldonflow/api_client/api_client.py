from seldonflow.util.config import Config

from abc import ABC, abstractmethod


class iApiClient(ABC):
    _api_keys: dict

    def __init__(self, config: Config):
        self._api_keys = self.get_api_keys_from_config(config)

    @abstractmethod
    def get_api_keys_from_config(self, config: Config) -> dict:
        pass

    @abstractmethod
    def get_market_data(self, market_id: str) -> dict:
        pass

    @abstractmethod
    def get_market_orderbook(self, market_id: str) -> dict:
        pass

    @abstractmethod
    def get_balances(self) -> dict:
        pass

    @abstractmethod
    def get_positions(self) -> dict:
        pass
