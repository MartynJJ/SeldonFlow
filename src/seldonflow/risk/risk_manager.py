from seldonflow.api_client.api_client import iApiClient
from seldonflow.util.logger import LoggingMixin
from seldonflow.util import custom_types


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


class RiskManager(LoggingMixin):
    _api_client: iApiClient
    _risk_detail: RiskDetail
    _TICK_INTERVAL_SECONDS: custom_types.TimeStamp = custom_types.TimeStamp(60)
    _next_tick_time: custom_types.TimeStamp = custom_types.TimeStamp(0.0)

    def __init__(self, api_client: iApiClient):
        super().__init__()
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

    def update_next_tick(self, current_time: custom_types.TimeStamp):
        self._next_tick_time = custom_types.TimeStamp(
            current_time + self._TICK_INTERVAL_SECONDS
        )

    def on_tick(self, current_time: custom_types.TimeStamp):
        if current_time < self._next_tick_time:
            return
        self.log_risk()
        self.update_next_tick(current_time)

    def log_risk(self):
        self.logger.info(f"{self.get_external_risk()}")
