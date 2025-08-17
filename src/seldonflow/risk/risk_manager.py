from seldonflow.api_client.api_client import iApiClient
from seldonflow.util.logger import LoggingMixin
from seldonflow.util import custom_types
from seldonflow.api_client.order import ExecutionOrder

from typing import List


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

    def get_execution_balance_required(self, order: ExecutionOrder) -> int:
        if order._side == custom_types.Side.SELL:
            return 0
        if order.venue == custom_types.Venue.KALSHI:
            notional = order.notional_cents()
            fee = order.fee_dollars()
            return notional + int(fee * 100)
        else:
            raise ValueError(f"Unexpected Venue: {order.venue}")

    def is_trade_valid(self, order: ExecutionOrder):
        balance_required = self.get_execution_balance_required(order=order)
        balance = int(100 * self._api_client.get_balances().get("USD", 0.0))
        if balance < balance_required:
            self.logger.info(
                f"Insufficient Balance: {order._order_id} - Balance: {balance} - Balance Required: {balance_required}"
            )
            return False
        else:
            return True

    def process_execution_requests(self, execution_orders: List[ExecutionOrder]):
        for execution_order in execution_orders:
            if self.is_trade_valid(execution_order):
                continue
