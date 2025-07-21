from seldonflow.util.config import Config
from seldonflow.api_client.kalshi_client import KalshiClient

import asyncio
from datetime import datetime


class LivePlatform:
    _config: Config
    _tick_length_seconds: int = 1
    _enabled: bool = False

    def __init__(self):
        self._config = Config()
        self.api_client = KalshiClient(config=self._config)

    async def on_tick(self, current_time: int):
        print(f"Current Time {current_time}")
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
