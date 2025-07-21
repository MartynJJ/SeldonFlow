from seldonflow.api_client.api_client import iApiClient


class RiskManager:
    _api_client: iApiClient

    def __init__(self, api_client: iApiClient):
        self._api_client = api_client

    def load_risk(self):
        print(f"Balances: {self._api_client.get_balances()}")

    def on_tick(self):
        self.load_risk()
