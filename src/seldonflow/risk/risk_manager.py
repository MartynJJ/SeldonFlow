from seldonflow.api_client.api_client import iApiClient


class RiskDetail:
    def __init__(self):
        self.balances = {}
        self.positions = {}

    def set_balances(self, balances):
        self.balances = balances

    def set_positions(self, positions):
        self.positions = positions

    def add_balance(self, ccy, amount):
        self.balances[ccy] = self.balances.get(ccy, 0.0) + amount

    def __eq__(self, other):
        if not isinstance(other, RiskDetail):
            return False
        return self.balances == other.balances

    def __repr__(self):
        return f"RiskDetail(balances={self.balances} positions={self.positions})"


class RiskManager:
    _api_client: iApiClient
    _risk_detail: RiskDetail

    def __init__(self, api_client: iApiClient):
        self._api_client = api_client
        self._risk_detail = RiskDetail()
        self.initial_external_position_load()

    def initial_external_position_load(self):
        self._risk_detail = self.get_external_risk()

    def get_risk(self):
        return self._risk_detail

    def get_external_risk(self):
        risk_detail = RiskDetail()
        risk_detail.set_balances(self._api_client.get_balances())
        risk_detail.set_positions(self._api_client.get_positions())
        return risk_detail

    def on_tick(self):
        print(self.get_risk())
