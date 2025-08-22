from seldonflow.util import custom_types

from abc import ABC, abstractmethod
from typing import Optional


class DataCollector(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def on_tick(self, current_time: custom_types.TimeStamp):
        pass

    @abstractmethod
    def collect_station_data(self, station: str) -> Optional[custom_types.Temp]:
        pass
