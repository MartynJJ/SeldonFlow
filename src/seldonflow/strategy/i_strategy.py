from seldonflow.util.custom_types import TimeStamp, Seconds

from abc import ABC, abstractmethod
from enum import Enum


class StrategyType(Enum):
    Invalid = 0
    StartOfDayTempPredict = 1
    TemperatureRestingOrderSweep = 2


class ActionRequest:
    def __init__(self, actions: list):
        self._actions = actions

    @staticmethod
    def no_action():
        return ActionRequest([])


class StrategyParams(ABC):
    _strategy_type: StrategyType
    _desc: str
    _tick_interval: Seconds

    def __init__(self, params_dict: dict):
        self._strategy_type = params_dict.get("strategy_type", StrategyType.Invalid)
        self._desc = params_dict.get("desc", "")
        self._tick_interval = params_dict.get("tick_interval", Seconds(0))

    def strategy_type(self):
        return self._strategy_type

    def tick_interval(self):
        return self._tick_interval


class iStrategy(ABC):

    def __init__(self, params: StrategyParams):
        self._params = params

    def type(self):
        return self._params.strategy_type()

    def tick_interval(self):
        return self._params.tick_interval()

    @abstractmethod
    def on_tick(self, time_stamp: TimeStamp) -> ActionRequest:
        pass
