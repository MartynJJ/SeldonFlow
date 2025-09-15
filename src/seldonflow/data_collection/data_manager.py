from seldonflow.util.logger import LoggingMixin
from seldonflow.util import custom_types
from seldonflow.data_collection.metar_data_collector import MetarCollector
from seldonflow.data_collection.nws_forecast_data_collector import NwsForecastCollector
from seldonflow.data_collection.nws_daily_summary import DailySummaryCollector
from seldonflow.data_collection.intraday_nws_data_collector import IntradayNwsCollector
from seldonflow.data_collection.data_collector import DataCollector
from seldonflow.data_collection.kalshi_order_book_collector import (
    KalshiOrderBookCollector,
)
from seldonflow.util.env import Environment
from seldonflow.api_client import kalshi_client
from typing import Dict, Optional


class DataManager(LoggingMixin):
    _data_collectors: Dict[str, DataCollector]

    def __init__(
        self,
        env: Environment = Environment.PRODUCTION,
        kalshi_api: Optional[kalshi_client.KalshiClient] = None,
    ):
        super().__init__()
        self._env = env
        self._data_collectors = {
            "MetarData": MetarCollector(self._env),
            "NwsForecast": NwsForecastCollector(self._env),
            "NWSDailySummary": DailySummaryCollector(env=self._env),
            "IntradayNWS": IntradayNwsCollector(env=self._env),
        }
        self._kalshi_api = kalshi_api
        self.load_kalshi_orderbook_collector()
        self.logger.info(f"Data Manager Initialized in {self._env}")

    def load_kalshi_orderbook_collector(self):
        if self._kalshi_api:
            self._data_collectors["KalshiOrderBook"] = KalshiOrderBookCollector(
                self._kalshi_api, self._env
            )
        else:
            self.logger.warning(
                f"Kalshi Order Book Collector not loaded as no api passed."
            )

    async def on_tick(self, current_time: custom_types.TimeStamp):
        for name, collector in self._data_collectors.items():
            await collector.on_tick(current_time=current_time)

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
