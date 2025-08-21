from seldonflow.api_client.api_client import iApiClient
from seldonflow.util.logger import LoggingMixin
from seldonflow.strategy.i_strategy import ActionRequest
from seldonflow.api_client.order import PredictionOrder
from typing import Dict, Any
from seldonflow.util import custom_types
from seldonflow.api_client.kalshi_client import KalshiClient


class ExecutionManager(LoggingMixin):
    _trading_enabled: bool = False
    _kalshi_client: KalshiClient

    def __init__(self, kalshi_client: KalshiClient):
        super().__init__()
        self._kalshi_client = kalshi_client
        self._trading_enabled = False

    def enable(self):
        self._trading_enabled = True

    def disable(self):
        self._trading_enabled = False

    def process_action_request(self, action_request: ActionRequest) -> Dict[str, Any]:
        execution_orders = action_request._executions
        for execution_order in execution_orders:
            if not self.is_trade_valid(execution_order):
                self.logger.warning(f"Invalid Trade {execution_order}")
                continue

        return {}

    def process_execution(self, execution_order: PredictionOrder) -> Dict[str, Any]:
        if execution_order.venue() == custom_types.Venue.KALSHI:
            response = self._kalshi_client.send_order(execution_order=execution_order)
            return response
        else:
            ValueError("Venue not enabled")
            return {}

    def get_execution_balance_required(self, order: PredictionOrder) -> int:
        if order._side == custom_types.Side.SELL:
            return 0
        if order.venue == custom_types.Venue.KALSHI:
            notional = order.notional_cents()
            fee = order.fee_dollars()
            return notional + int(fee * 100)
        else:
            raise ValueError(f"Unexpected Venue: {order.venue}")

    def is_trade_valid(self, order: PredictionOrder):
        balance_required = self.get_execution_balance_required(order=order)
        balance = int(100 * self._kalshi_client.get_balances().get("USD", 0.0))
        if balance < balance_required:
            self.logger.info(
                f"Insufficient Balance: {order._order_id} - Balance: {balance} - Balance Required: {balance_required}"
            )
            return False
        else:
            return True
