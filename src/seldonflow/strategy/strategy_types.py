from enum import Enum


class StrategyType(Enum):
    Invalid = 0
    StartOfDayTempPredict = 1
    TemperatureRestingOrderSweep = 2
    MaxTempNYC = 3

    @classmethod
    def from_string(cls, strategy_type_str):
        if strategy_type_str.lower() == "startofdaytemppredict":
            return cls.StartOfDayTempPredict
        if strategy_type_str.lower() == "temperaturerestingordersweep":
            return cls.TemperatureRestingOrderSweep
        if strategy_type_str.lower() == "maxtempnyc":
            return cls.MaxTempNYC
        else:
            return cls.Invalid
