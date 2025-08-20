from seldonflow.util.logger import LoggingMixin
from seldonflow.util import custom_types
from seldonflow.data_collection.metar_data_collector import MetarCollector
from seldonflow.data_collection.nws_forecast_data_collector import NwsForecastCollector
from seldonflow.data_collection.nws_daily_summary import DailySummaryCollector
from seldonflow.data_collection.data_collector import DataCollector
from seldonflow.util.env import Environment

from typing import Dict


class DataManager(LoggingMixin):
    _data_collectors: Dict[str, DataCollector]

    def __init__(self, env: Environment = Environment.PRODUCTION):
        super().__init__()
        self._env = env
        self._data_collectors = {
            "MetarData": MetarCollector(self._env),
            "NwsForecast": NwsForecastCollector(self._env),
            "NWSDailySummary": DailySummaryCollector(env=self._env),
        }
        self.logger.info(f"Data Manager Initialized in {self._env}")

    def on_tick(self, current_time: custom_types.TimeStamp):
        for name, collector in self._data_collectors.items():
            collector.on_tick(current_time=current_time)

    def metar_data(self) -> DataCollector:
        try:
            return self._data_collectors["MetarData"]
        except KeyError as e:
            self.logger.error(f"MetarData collector not found: {e}")
            raise

    def nws_forecast_data(self) -> DataCollector:
        try:
            return self._data_collectors["NwsForecast"]
        except KeyError as e:
            self.logger.error(f"NwsForecast collector not found: {e}")
            raise
