from seldonflow.util.custom_types import TimeStamp, Seconds
from seldonflow.util.config import Config, ConfigType
from seldonflow.strategy.strategy_types import StrategyType

from abc import ABC, abstractmethod


class ActionRequest:
    def __init__(self, actions: list):
        self._actions = actions

    @staticmethod
    def no_action():
        return ActionRequest([])


class StrategyParams:
    _strategy_type: StrategyType
    _desc: str
    _name: str
    _tick_interval: Seconds
    _live: bool

    def __init__(self, name: str, params_dict: dict):
        self._name = name
        self._strategy_type = params_dict.get("strategy_type", StrategyType.Invalid)
        self._desc = params_dict.get("desc", "")
        self._tick_interval = params_dict.get("tick_interval", Seconds(0))
        self._live = params_dict.get("live", False)
        self._extra_params = self.parse_extra_params(params_dict.get("parameters", {}))
        self._raw = params_dict

    @staticmethod
    def parse_extra_params(extra_params: list[dict]):
        extra_params_return = dict()
        for extra_param in extra_params:
            extra_params_return[extra_param.get("name", "")] = extra_param
        return extra_params_return

    def get_params(self) -> dict:
        return self._extra_params

    def get_attribute(self, attribute: str):
        return self._raw.get(attribute, "")

    def strategy_type(self) -> StrategyType:
        return self._strategy_type

    def tick_interval(self) -> Seconds:
        return self._tick_interval

    def name(self) -> str:
        return self._name

    def __repr__(self):
        return f"StrategyParams(name={self._name}, type={self._strategy_type}, desc={self._desc}, tick_interval={self._tick_interval}, live={self._live}, params={self._extra_params})"


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


class InvalidStrategy(iStrategy):
    def __init__(self, params: StrategyParams):
        super().__init__(params)

    def on_tick(self, time_stamp: TimeStamp) -> ActionRequest:
        return ActionRequest.no_action()

    @staticmethod
    def create():
        return InvalidStrategy(StrategyParams("Invalid", {}))


def main():
    config = Config()
    for name, param_dict in config.strategies().items():
        strategy_param = StrategyParams(name, param_dict)
        print(strategy_param)


if __name__ == "__main__":
    main()
