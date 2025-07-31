from seldonflow.util.config import Config
from seldonflow.api_client.api_client import iApiClient

import kalshi


class KalshiClient(iApiClient):
    def __init__(self, config: Config):
        super().__init__(config)
        self.public_key_id = self._api_keys["public_key_id"]
        self.private_key_path = self._api_keys["private_key_path"]

        kalshi.auth.set_key(
            access_key=self.public_key_id,
            private_key_path=self.private_key_path,
        )
        self.api = kalshi.rest

    def get_api_keys_from_config(self, config: Config) -> dict:
        return config.get_api_key("kalshi")

    def get_market_data(self, market_id: str) -> dict:
        """Fetch the orderbook for a given market ID."""
        return self.api.market.GetMarket(market_id)

    def get_market_orderbook(self, market_id: str) -> dict:
        """Fetch the orderbook for a given market ID."""
        return self.api.market.GetMarketOrderbook(market_id)

    def get_balances(self) -> dict:
        balance = self.api.portfolio.GetBalance()
        return {"USD": balance["balance"] / 100}

    def get_positions(self) -> dict:
        positions_raw = self.api.portfolio.GetPositions()
        return self.format_kalshi_positions(positions_raw=positions_raw)

    def format_kalshi_positions(self, positions_raw: dict):
        positions = positions_raw.get("market_positions", [])
        return positions
