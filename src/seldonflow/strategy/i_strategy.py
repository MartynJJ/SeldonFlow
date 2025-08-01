from seldonflow.util.types import TimeStamp, Seconds

from abc import ABC, abstractmethod
from enum import Enum


class StrategyType(Enum):
    Invalid = 0
    TempPredict = 1


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

    def __init__(self, strategy_type: StrategyType, desc: str, tick_interval: Seconds):
        self._strategy_type = strategy_type
        self._desc = desc
        self._tick_interval = tick_interval


class iStrategy(ABC):

    def __init__(self, params: StrategyParams):
        self._params = params

    @abstractmethod
    def on_tick(self, time_stamp: TimeStamp) -> ActionRequest:
        pass
