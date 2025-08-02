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


class StrategyManager:
    _platform: iPlatform
    _strategy_params: list[StrategyParams] = []
    _strategies: dict[str, iStrategy]

    def __init__(self, platform: iPlatform, config: Config):
        self._platform = platform
        self.set_strategy_params(config=config)

    def set_strategy_params(self, config: Config):
        strategy_configs = config.strategies()
        for name, strategy_config in strategy_configs.items():
            self._strategy_params.append(StrategyParams(name, strategy_config))

    def load_strategies(self):
        for strategy_param in self._strategy_params:
            self._strategies[strategy_param.name()] = self.load_strategy(
                strategy_param=strategy_param, platform=self._platform
            )

    @staticmethod
    def load_strategy(strategy_param: StrategyParams, platform: iPlatform) -> iStrategy:
        if strategy_param.strategy_type == StrategyType.TemperatureRestingOrderSweep:
            return TROS(strategy_param, platform)
        return InvalidStrategy.create()


def main():
    platform = iPlatform()
    config = Config()
    strategy_manager = StrategyManager(platform, config)


if __name__ == "__main__":
    main()
