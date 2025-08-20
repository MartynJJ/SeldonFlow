from seldonflow.api_client import trading_api_client
from seldonflow.util.config import Config

from typing import Dict, Any


class GeminiClient(trading_api_client.iTradingClient):
    def __init__(
        self, config: Config, trading_access: trading_api_client.TradingAccess
    ):
        super().__init__(config=config, access=trading_access)

    def get_api_keys_from_config(self, config: Config) -> Dict[str, Any]:
        return {}

    def send_order_helper(self, trading_order: trading_api_client.TradingOrder):
        pass

    def get_positions(self) -> dict:
        return {}

    def get_ticker_info(self, ticker: str):
        pass
