from seldonflow.util.custom_types import TimeStamp, Temp, TempF
from seldonflow.strategy.i_strategy import (
    iStrategy,
    StrategyParams,
    ActionRequest,
    StrategyType,
)
from seldonflow.platform.i_platform import iPlatform


class TROS(iStrategy):
    def __init__(self, params: StrategyParams, platform: iPlatform):
        super().__init__(params)
        self._platform = platform

    def on_tick(self, time_stamp: TimeStamp) -> ActionRequest:
        return ActionRequest.no_action()

    def get_max_observed_temperate(self) -> Temp:
        return Temp.from_f(TempF(98.0))

    def get_resting_orders(self):
        api_client = self._platform.api_client()
        api_client.get_market_orderbook("")
        pass
