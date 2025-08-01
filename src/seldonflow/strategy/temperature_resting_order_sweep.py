from seldonflow.util.custom_types import TimeStamp, Temp, TempF
from seldonflow.strategy.i_strategy import (
    iStrategy,
    StrategyParams,
    ActionRequest,
    StrategyType,
)


class TROSParams(StrategyParams):
    def __init__(self, params_dict: dict):
        super().__init__(params_dict)
        assert self.strategy_type() == StrategyType.TemperatureRestingOrderSweep


class TROS(iStrategy):
    def __init__(self, params: StrategyParams):
        super().__init__(params)

    def on_tick(self, time_stamp: TimeStamp) -> ActionRequest:
        return ActionRequest.no_action()

    def get_max_observed_temperate(self) -> Temp:
        return Temp.from_f(TempF(98.0))

    def get_resting_orders(self):
        pass
