from seldonflow.util.logger import LoggingMixin
from seldonflow.util.config import Config

from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum


class TradingAccess(Enum):
    Invalid = 0
    Full = 1
    ReadOnly = 2


class TradingOrder:
    def __init__(self):
        pass


class iTradingClient(ABC, LoggingMixin):

    def __init__(self, config: Config, access: TradingAccess = TradingAccess.ReadOnly):
        super().__init__()
        self._api_keys = self.get_api_keys_from_config(config)
        self._access = access

    @abstractmethod
    def get_api_keys_from_config(self, config: Config) -> Dict[str, Any]:
        pass

    def access(self):
        return self._access

    def has_trading_access(self) -> bool:
        return self._access == TradingAccess.Full

    def send_order(self, trading_order: TradingOrder):
        if self.has_trading_access():
            self.send_order_helper(trading_order=trading_order)
        else:
            self.logger.warning(f"Attempting to trade without Trading Permission")

    @abstractmethod
    def send_order_helper(self, trading_order: TradingOrder):
        pass

    @abstractmethod
    def get_positions(self) -> dict:
        pass

    @abstractmethod
    def get_ticker_info(self, ticker: str):
        pass


def main():
    pass
    # class Temp(iTradingClient):
    #     def __init__(self):
    #         super().__init__()

    # client = Temp()
    # print(client.logger.level)


if __name__ == "__main__":
    main()
