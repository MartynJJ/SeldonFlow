from seldonflow.platform.i_platform import iPlatform
from seldonflow.strategy.i_strategy import (
    iStrategy,
    StrategyParams,
    ActionRequest,
    InvalidStrategy,
)
from seldonflow.util.config import Config, ConfigType
from seldonflow.strategy.strategy_types import StrategyType
from seldonflow.strategy.temperature_resting_order_sweep import TROS
from seldonflow.util.logger import LoggingMixin
from datetime import date
from seldonflow.util import custom_types


class StrategyManager(LoggingMixin):
    _platform: iPlatform
    _strategy_params: list[StrategyParams] = []
    _strategies: dict[str, iStrategy] = {}

    def __init__(self, platform: iPlatform, config: Config, today: date):
        super().__init__()
        self._date = date
        self._platform = platform
        self.set_strategy_params(config=config)

    def set_strategy_params(self, config: Config):
        strategy_configs = config.strategies()
        for name, strategy_config in strategy_configs.items():
            self._strategy_params.append(StrategyParams(name, strategy_config))

    def load_strategies(self):
        for strategy_param in self._strategy_params:
            self.logger.info(
                f"Loading Strategy: {strategy_param.name()} - {strategy_param.strategy_type()}"
            )
            self._strategies[strategy_param.name()] = self.load_strategy(
                strategy_param=strategy_param, platform=self._platform
            )
            self.logger.info(f"{strategy_param.name()} loaded")
        self.logger.info(f"{len(self._strategies)} strategy loaded: {self._strategies}")

    def load_strategy(
        self, strategy_param: StrategyParams, platform: iPlatform
    ) -> iStrategy:
        if strategy_param.strategy_type() == StrategyType.TemperatureRestingOrderSweep:
            return TROS(
                strategy_param,
                platform.api_client(),
                platform.today(),
                platform.data_manager(),
            )
        else:
            self.logger.warning(
                f"Strategy Not Loaded: {strategy_param.name()} {strategy_param.strategy_type()}"
            )
            return InvalidStrategy.create()

    def on_tick(self, current_time: custom_types.TimeStamp):
        for _, strategy in self._strategies.items():
            action_request = strategy.on_tick(current_time)


def main():
    pass
    # platform = iPlatform()
    # config = Config()
    # strategy_manager = StrategyManager(platform, config)


if __name__ == "__main__":
    main()
