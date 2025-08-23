from seldonflow.data_collection import data_collector
from seldonflow.util.logger import LoggingMixin
from seldonflow.util.env import Environment
from seldonflow.api_client.kalshi_client import KalshiClient
from seldonflow.util import ticker_mapper
from seldonflow.util import custom_methods, custom_types
from seldonflow.data_collection import kalshi_order_book_utils
from seldonflow.util import tick_manager, ticker_mapper

import datetime
from typing import Optional, List
from pathlib import Path
import pandas as pd
import asyncio

ORDER_BOOK_FILE_DIR = Path("src/seldonflow/data/shared/kalshi/historic_orderbook/")
DEV_ORDER_BOOK_FILE_DIR = Path(
    "src/seldonflow/data/shared/DEV/kalshi/historic_orderbook/"
)


class KalshiOrderBookCollector(LoggingMixin, data_collector.DataCollector):
    def __init__(
        self, kalshi_client: KalshiClient, env: Environment = Environment.PRODUCTION
    ):
        super().__init__()
        self._env = env
        self._kalshi_client = kalshi_client
        self._base_ticker = self.get_base_tickers()
        self._save_dir = (
            ORDER_BOOK_FILE_DIR
            if self._env == Environment.PRODUCTION
            else DEV_ORDER_BOOK_FILE_DIR
        )
        self._tick_manager = tick_manager.TickManager(tick_manager.ONE_MINUTE)
        self._enabled = True
        self.logger.info(
            f"Kalshi Orderbook Collector Loaded: {self._env} Tick Interval: {self._tick_manager._tick_interval}"
        )

    def get_base_tickers(self):
        temp_locations = [ticker_mapper.TempLocation.NYC]
        temp_tickers = [
            ticker_mapper.KALSHI_MAX_TEMP_LOCATION_TO_TICKER.get(location)
            for location in temp_locations
        ]
        return temp_tickers

    def get_active_tickers(
        self, time_stamp: Optional[custom_types.TimeStamp] = None
    ) -> List[str]:
        if not time_stamp:
            time_stamp = custom_types.TimeStamp(datetime.datetime.now().timestamp())
        today = custom_methods.time_stamp_to_NYC(time_stamp=time_stamp).date()
        todays_tickers = []
        tomorrows_tickers = []
        for base_ticker in self._base_ticker:
            if base_ticker:
                todays_tickers += self._kalshi_client.get_active_tickers(
                    base_ticker=base_ticker, event_date=today
                )
                tomorrows_tickers += self._kalshi_client.get_active_tickers(
                    base_ticker=base_ticker,
                    event_date=today + datetime.timedelta(days=1),
                )
        fed_decision_tickers = self._kalshi_client.get_active_tickers_for_series(
            ticker_mapper.FED_EVENT_TICKER
        )
        return todays_tickers + tomorrows_tickers

    def get_ticker_orderbook_df(
        self, ticker: str, time_stamp: Optional[custom_types.TimeStamp] = None
    ):
        if not time_stamp:
            time_stamp = custom_types.TimeStamp(datetime.datetime.now().timestamp())
        df = kalshi_order_book_utils.create_orderbook_dataframe(
            timestamp=time_stamp,
            orderbook_data=self._kalshi_client.get_market_orderbook(ticker),
        )
        return df

    def get_ticker_orderbook_filename(self, ticker: str) -> Path:
        return self._save_dir / f"OrderBook_{ticker}.csv"

    def load_ticker_df(self, ticker: str) -> Optional[pd.DataFrame]:
        file_path = self.get_ticker_orderbook_filename(ticker=ticker)
        if file_path.is_file():
            try:
                loaded_df = pd.read_csv(file_path, index_col=0).astype("int32")
                loaded_df.columns = kalshi_order_book_utils._COLUMN_RANGE
                return loaded_df
            except Exception as error:
                self.logger.error(
                    f"Error Loading Ticker Orderbook : {error} - {file_path}"
                )
                return None
        else:
            return None

    async def load_orderbook_if_exists_and_save_new_timepoint(
        self, ticker: str, time_stamp: Optional[custom_types.TimeStamp] = None
    ):
        file_path = self.get_ticker_orderbook_filename(ticker=ticker)
        new_orderbook = self.get_ticker_orderbook_df(
            ticker=ticker, time_stamp=time_stamp
        )
        file_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if file_path.is_file() else "w"
        header = not file_path.is_file()

        try:
            new_orderbook.to_csv(file_path, mode=mode, header=header, index=True)
        except Exception as error:
            self.logger.error(f"Error saving orderbook for {ticker}: {error}")

    async def load_all_orderbooks_and_save(
        self, time_stamp: Optional[custom_types.TimeStamp] = None
    ):
        active_tickers = self.get_active_tickers()
        if not time_stamp:
            time_stamp = custom_types.TimeStamp(datetime.datetime.now().timestamp())

        tasks = [
            self.load_orderbook_if_exists_and_save_new_timepoint(
                ticker=ticker, time_stamp=time_stamp
            )
            for ticker in active_tickers
        ]
        results = await asyncio.gather(*tasks)
        return results

    async def on_tick(self, current_time: custom_types.TimeStamp):
        if self._enabled and self._tick_manager.ready_with_auto_update(current_time):
            try:
                await self.load_all_orderbooks_and_save(time_stamp=current_time)
            except Exception as error:
                self.logger.error(f"Error Pulling Orderbooks, disabling: {error}")
                self._enabled = False

    def collect_station_data(self, station: str) -> Optional[custom_types.Temp]:
        return None
