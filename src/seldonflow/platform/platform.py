from seldonflow.util.config import Config
from seldonflow.api_client.kalshi_client import KalshiClient
from seldonflow.api_client.api_client import iApiClient
from seldonflow.risk.risk_manager import RiskManager
from seldonflow.execution.execution_manager import ExecutionManager

import asyncio
from datetime import datetime, date


class LivePlatform:
    _config: Config
    _tick_length_seconds: int = 1
    _enabled: bool = False
    _api_client: iApiClient
    _risk_manager: RiskManager
    _execution_manager: ExecutionManager

    def __init__(self):
        self._config = Config()
        self._api_client = KalshiClient(config=self._config)
        self._risk_manager = RiskManager(self.api_client())
        self._execution_manager = ExecutionManager(self.api_client())

    def api_client(self) -> iApiClient:
        return self._api_client

    async def on_tick(self, current_time: int):
        print(f"Current Time {current_time}")
        self._risk_manager.on_tick()
        return

    async def run(self):
        while True:
            current_time = self.get_current_time()
            await self.on_tick(current_time)
            await asyncio.sleep(self._tick_length_seconds)

    def get_current_time(self) -> int:
        # use abstract method base class if simulation is implemented.
        return int(datetime.now().timestamp())

    def enable(self):
        self._enabled = True
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            print("Stopped by user")
            self._enabled = False
