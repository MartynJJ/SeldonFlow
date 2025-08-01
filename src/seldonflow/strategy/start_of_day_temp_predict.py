from seldonflow.strategy.i_strategy import (
    iStrategy,
    StrategyParams,
    StrategyType,
    ActionRequest,
)
from seldonflow.util.custom_types import TimeStamp, Temp, TempF

from typing import NamedTuple


class TemperaturePrediction(NamedTuple):
    temperature: Temp
    confidence: float


def run_temp_prediction_model() -> TemperaturePrediction:
    return TemperaturePrediction(Temp.from_f(TempF(97.0)), 0.0)


class StartOfDayTempPredict(iStrategy):
    def __init__(self, params: StrategyParams):
        super().__init__(params)

    def on_tick(self, time_stamp: TimeStamp) -> ActionRequest:
        return ActionRequest.no_action()

    def predict_temp_central_park(self):
        max_temp, confidence = run_temp_prediction_model()
