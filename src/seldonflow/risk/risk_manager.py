from seldonflow.api_client.api_client import iApiClient
from seldonflow.api_client import kalshi_client
from seldonflow.util.config import Config
from seldonflow.util.logger import LoggingMixin
from seldonflow.util import custom_types
from seldonflow.api_client.order import ExecutionOrder

from typing import List, Optional, Dict, Any


def get_strategy_risk_params(strategy_param: Dict[str, Any]) -> Dict[str, Any]:
    extra_params = strategy_param.get("parameters", [])
    for param in extra_params:
        if param.get("name", "") == "Risk":
            return param
    return {}


class StrategyRisk(LoggingMixin):
    def __init__(
        self,
        strategy_name: str,
        currency: custom_types.Currency,
        max_value_at_risk: float,
    ):
        super().__init__()
        self._strategy_name = strategy_name
        self._currency = currency
        self._value_at_risk = 0.0
        self._max_value_at_risk = max_value_at_risk

    def value_at_risk_remaining(self) -> float:
        return self._max_value_at_risk - self._value_at_risk

    def add_value_at_risk(self, value_at_risk: float):
        self._value_at_risk += value_at_risk


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
    _risk_detail_by_venue: Dict[custom_types.Venue, Optional[RiskDetail]] = {}
    _TICK_INTERVAL_SECONDS: custom_types.TimeStamp = custom_types.TimeStamp(60)
    _next_tick_time: custom_types.TimeStamp = custom_types.TimeStamp(0.0)
    _kalshi_client: Optional[kalshi_client.KalshiClient] = None
    _strategy_risk_by_strategy: Dict[str, StrategyRisk] = {}

    def __init__(
        self,
        kalshi_client: Optional[kalshi_client.KalshiClient] = None,
        config: Optional[Config] = None,
    ):
        super().__init__()
        self._kalshi_client = kalshi_client
        self._config = config
        self.initial_external_position_load()

    def initial_external_position_load(self):
        self.set_external_risk_by_venue()

    def get_risk(self) -> Dict[custom_types.Venue, Optional[RiskDetail]]:
        return self._risk_detail_by_venue

    def get_external_kalshi_risk(self) -> Optional[RiskDetail]:
        if self._kalshi_client:
            kalshi_risk_detail = RiskDetail()
            kalshi_risk_detail.set_balances(self._kalshi_client.get_balances())
            kalshi_risk_detail.set_positions(self._kalshi_client.get_positions())
            return kalshi_risk_detail
        else:
            return None

    def set_external_risk_by_venue(self):
        self._risk_detail_by_venue[custom_types.Venue.KALSHI] = (
            self.get_external_kalshi_risk()
        )

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
        self.logger.info(f"{self.get_risk()}")

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
        strategy_name = order._strategy
        balance_required = self.get_execution_balance_required(order=order)
        balance = int(100 * self._api_client.get_balances().get("USD", 0.0))
        if balance < balance_required:
            self.logger.info(
                f"Insufficient Balance: {order._order_id} - Balance: {balance} - Balance Required: {balance_required}"
            )
            return False
        if strategy_name and (strategy_name in self._strategy_risk_by_strategy.keys()):
            strategy_risk = self._strategy_risk_by_strategy[strategy_name]
            var_remaining = strategy_risk.value_at_risk_remaining()
            if balance_required > var_remaining:
                return False
        return True

    def process_execution_requests(self, execution_orders: List[ExecutionOrder]):
        for execution_order in execution_orders:
            strategy_name = execution_order._strategy
            if self.is_trade_valid(execution_order):
                continue

    def set_strategy_risk(self) -> None:
        if self._config:
            for strategy_name, strategy_param in self._config.strategies().items():
                params = get_strategy_risk_params(strategy_param=strategy_param)
                self._strategy_risk_by_strategy[strategy_name] = StrategyRisk(
                    strategy_name=strategy_name,
                    currency=params.get("risk_currency", ""),
                    max_value_at_risk=params.get("max_value_at_risk", 0.0),
                )
        else:
            self.logger.warning("No Config Found - Cannot Load Risk Params")
