from seldonflow.strategy.i_strategy import ActionRequest
from seldonflow.util.config import Config
from seldonflow.api_client.kalshi_client import KalshiClient
from seldonflow.api_client.api_client import iApiClient
from seldonflow.risk.risk_manager import RiskManager
from seldonflow.execution.execution_manager import ExecutionManager
from seldonflow.strategy.strategy_manager import StrategyManager
from seldonflow.platform.i_platform import iPlatform
from seldonflow.util import env
from seldonflow.util import custom_types
import asyncio
from datetime import datetime, date
from seldonflow.util.logger import LoggingMixin
from seldonflow.data_collection.data_manager import DataManager


class LivePlatform(iPlatform):
    _config: Config
    _tick_length_seconds: int = 1
    _enabled: bool = False
    _api_client: iApiClient
    _risk_manager: RiskManager
    _execution_manager: ExecutionManager
    _strategy_manager: StrategyManager
    _data_manager: DataManager
    _today: date = datetime.today().date()

    def __init__(self, environment: env.Environment):
        super().__init__(environment=environment)
        self._today = datetime.today().date()
        self._config = Config()
        self._api_client = KalshiClient(config=self._config)
        self._risk_manager = RiskManager(self._api_client, self._config)
        self._execution_manager = ExecutionManager(self._api_client)
        self._strategy_manager = StrategyManager(self, self._config, self.today())
        self._data_manager = DataManager()

    def today(self) -> date:
        return self._today

    def api_client(self) -> iApiClient:
        return self._api_client

    async def on_tick(self, current_time: custom_types.TimeStamp):
        self._risk_manager.on_tick(current_time)
        self._strategy_manager.on_tick(current_time)
        self._data_manager.on_tick(current_time=current_time)
        return

    async def run(self):
        while True:
            current_time = self.get_current_time()
            await self.on_tick(current_time)
            await asyncio.sleep(self._tick_length_seconds)

    def get_current_time(self) -> custom_types.TimeStamp:
        # use abstract method base class if simulation is implemented.
        return custom_types.TimeStamp(datetime.now().timestamp())

    def enable(self):
        self._strategy_manager.load_strategies()
        self._enabled = True
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            print("Stopped by user")
            self._enabled = False

    def receive_action_request(self, action_request: ActionRequest):
        self.logger.info(
            f"Processing Action Request: Executions: {len(action_request._executions)}"
        )
        results = self._execution_manager.process_action_request(action_request)

    def data_manager(self) -> DataManager:
        return self._data_manager


def main():
    platform = LivePlatform(env.Environment.TESTING)
    print(f"{platform._strategy_manager._strategy_params}")


if __name__ == "__main__":
    main()
