from seldonflow.util.config import Config, ConfigType

import kalshi_python
import kalshi.auth
import kalshi.rest
import kalshi.websocket
import yaml

KALSHI = "kalshi"


class KalshiClient:
    DEMO_END_POINT = "https://demo-api.kalshi.co/trade-api/v2"
    LIVE_END_POINT = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self, config: Config, demo: bool = False):
        self._keys = self.get_api_keys_from_config(config)
        self._demo = demo
        self._api = self.auth()

    def auth(self):
        kalshi_sdk_config = kalshi_python.Configuration()
        if self._demo:
            kalshi_sdk_config.host = KalshiClient.DEMO_END_POINT
        else:
            kalshi_sdk_config.host = KalshiClient.LIVE_END_POINT
        return kalshi_python.ApiInstance(
            email=self._keys["email"],
            password=self._keys["password"],
            configuration=kalshi_sdk_config,
        )

    @staticmethod
    def get_api_keys_from_config(config: Config):
        api_keys = config.api_keys()
        assert len(api_keys) > 0
        assert KALSHI in api_keys.keys()
        kalshi_api_keys = api_keys[KALSHI]
        assert "email" in kalshi_api_keys.keys()
        assert "password" in kalshi_api_keys.keys()
        return kalshi_api_keys

    def get_series(self, series: str):
        return self._api.get_series(series)

    def get_market(self, market: str):
        return self._api.get_market(market)

    def get_positions(self):
        return self._api.get_positions()

    def test(self):
        kalshi.auth()
        # self._api.api_client.call_api
        return self._api.api_client.call_api(
            "https://api.elections.kalshi.com/trade-api/v2/markets",
        )


def main():
    config = Config()
    client = KalshiClient(config=config)
    # print(f"{client._keys}")
    print(f"{client._api.get_exchange_status()}")
    # print(f"{client.get_series('KXRATECUTCOUNT')}")
    print(f"{client.test()}")


if __name__ == "__main__":
    main()
