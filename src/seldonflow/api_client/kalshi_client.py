import kalshi
from seldonflow.util.config import Config


class KalshiClient:
    def __init__(self, config: Config):
        api_keys = config.get_api_key("kalshi")
        self.public_key_id = api_keys["public_key_id"]
        self.private_key_path = api_keys["private_key_path"]

        kalshi.auth.set_key(
            access_key=self.public_key_id,
            private_key_path=self.private_key_path,
        )
        self.api = kalshi.rest

    def get_market_data(self, market_id: str) -> dict:
        """Fetch the orderbook for a given market ID."""
        return self.api.market.GetMarket(market_id)

    def get_market_orderbook(self, market_id: str) -> dict:
        """Fetch the orderbook for a given market ID."""
        return self.api.market.GetMarketOrderbook(market_id)
