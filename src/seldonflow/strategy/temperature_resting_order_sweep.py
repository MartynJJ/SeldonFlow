from seldonflow.util.custom_types import (
    TimeStamp,
    Temp,
    TempF,
    Side,
    MarketSide,
    OrderType,
    Price,
)
from seldonflow.strategy.i_strategy import (
    iStrategy,
    StrategyParams,
    ActionRequest,
    StrategyType,
)
from seldonflow.api_client.api_client import iApiClient
from seldonflow.api_client.order import KalshiOrder
from seldonflow.util.ticker_mapper import (
    TempTickerEvent,
    KALSHI_MAX_TEMP_TICKER_TO_LOCATION,
    KALSHI_MAX_TEMP_LOCATION_TO_TICKER,
    TempLocation,
)
from seldonflow.fees import kalshi_fees
from seldonflow.data_collection import metar_data_collector
from seldonflow.data_collection.data_manager import DataCollector, DataManager

from datetime import date, time, datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import math


ABSOLUTE_ZERO = Temp.from_f(TempF(-459.67))


class TROS(iStrategy):
    _active_tickers: list[TempTickerEvent] = []
    _max_notional_cents = 1000
    _TICK_INTERVAL_SECONDS: TimeStamp = TimeStamp(60)
    _next_tick_time: TimeStamp = TimeStamp(0.0)
    _loaded: bool = False
    _start_time = time(14, 0, 0)
    _end_time = time(22, 0, 0)

    def __init__(
        self,
        params: StrategyParams,
        api_client: iApiClient,
        today: date,
        data_manager: DataManager,
    ):
        super().__init__(params)
        self._api_client = api_client
        self._location = self.get_location_from_params(params)
        self._base_ticker = KALSHI_MAX_TEMP_LOCATION_TO_TICKER.get(self._location, "")
        self._event_info = {}
        self._max_observed = ABSOLUTE_ZERO
        self._today = today
        self._data_manager = data_manager
        self.logger.info(f"TROS Loaded: {self}")

    def is_timestamp_in_window(self, time_stamp: TimeStamp):
        as_time = datetime.fromtimestamp(time_stamp).time()
        return (self._start_time < as_time) and (as_time < self._end_time)

    def __repr__(self) -> str:
        return f"TROS(location={self._location}, base_ticker={self._base_ticker}, max_observed={self._max_observed})"

    def set_next_tick_time(self, next_tick_time: TimeStamp):
        self._next_tick_time = next_tick_time

    def TICK_INTERVAL_SECONDS(self) -> TimeStamp:
        return self._TICK_INTERVAL_SECONDS

    @staticmethod
    def get_location_from_params(params):
        return TempLocation.from_string(
            params.get_params().get("Market", {}).get("location", "")
        )

    def initial_load(self):
        self.get_all_active_tickers()
        self._loaded = True

    def on_tick(self, current_time: TimeStamp) -> Optional[ActionRequest]:
        if current_time < self._next_tick_time:
            return None
        if not self.is_timestamp_in_window(current_time):
            return None
        self.logger.info(f"Evaluating TROS")
        if not self._loaded:
            self.initial_load()
        self.set_max_observed_temperature(current_time)
        execution_list = self.generate_execution_list()
        executions = []
        for possible_execution in execution_list:
            if possible_execution.get("net_winnings", -1) > 0:
                try:
                    executions.append(possible_execution["exeuction_order"])
                except KeyError as key_error:
                    print(f"Key Error: {key_error}")
        self.update_next_tick(current_time=current_time)
        return ActionRequest([], executions=executions)

    def get_current_temperature(self) -> Temp:
        station = metar_data_collector.TEMP_LOCATION_TO_STATION.get(self._location, "")
        current_temp_opt = self._data_manager.metar_data().collect_station_data(
            station=station
        )
        return current_temp_opt if current_temp_opt else ABSOLUTE_ZERO

    def get_max_observed_temperature(self, time_stamp: TimeStamp) -> Temp:
        station = metar_data_collector.TEMP_LOCATION_TO_STATION.get(self._location, "")
        if len(station):
            file_date = datetime.fromtimestamp(time_stamp)
            file_name = metar_data_collector.get_data_filename(
                station=station, date=file_date
            )
            df = pd.read_csv(file_name)
            max_temp = math.floor(df["TempF"].max())
            current_temp = self.get_current_temperature().as_fahrenheit()
            actual_max = max(max_temp, current_temp)
            return Temp.from_f(TempF(actual_max))
        else:
            return ABSOLUTE_ZERO

    def set_max_observed_temperature(self, time_stamp: TimeStamp) -> None:
        self._max_observed = self.get_max_observed_temperature(time_stamp)

    def get_all_active_tickers(self):
        self._event_info = self._api_client.get_event(self._base_ticker, self._today)
        markets = self._event_info.get("markets", [])
        for market in markets:
            self._active_tickers.append(TempTickerEvent(market))
        self.logger.info(f"Active Tickers: {self._active_tickers}")

    def get_resting_orders(self, ticker):
        return self._api_client.get_market_orderbook(ticker)

    def get_active_markets_below_current_max(self):
        tickers = []
        for ticker in self._active_tickers:
            if ticker.cap_strike.as_fahrenheit() < self._max_observed.as_fahrenheit():
                tickers.append(ticker)
        self.logger.info(f"Tickers Below Current Max: {tickers}")
        return tickers

    def get_yes_resting_orders_below_current(self):
        tickers = self.get_active_markets_below_current_max()
        opportunities = {}
        for ticker in tickers:
            orderbook = self.get_resting_orders(ticker.ticker).get("orderbook", {})
            yes_orders = orderbook.get("yes", {})
            opportunities[ticker] = yes_orders
        return opportunities

    def generate_execution_list(self) -> List[Dict[str, Any]]:
        opportunities = self.get_yes_resting_orders_below_current()
        uncertainty = 0.01
        orders = []
        for ticker, yes_orderbook in opportunities.items():

            if yes_orderbook == None:
                print(f"{ticker.ticker} : No Opps")
                continue
            for yes_price_cents, size in yes_orderbook:
                yes_price_dollars = yes_price_cents * 0.01
                no_price_dollars = 1.0 - yes_price_dollars

                winnings_for_no = (yes_price_dollars - uncertainty) * size
                fees = kalshi_fees.calculate_fee(no_price_dollars, size)
                notional = size * no_price_dollars * 100
                size = (
                    size
                    if notional <= self._max_notional_cents
                    else int(self._max_notional_cents / (100 * no_price_dollars))
                )
                net_winnings = winnings_for_no - fees
                if net_winnings > 0:
                    orders.append(
                        {
                            "net_winnings": net_winnings,
                            "exeuction_order": KalshiOrder(
                                ticker=ticker.ticker,
                                market_side=MarketSide.NO,
                                side=Side.BUY,
                                count=size,
                                order_type=OrderType.LIMIT,
                                price=Price(no_price_dollars),
                            ),
                        }
                    )
        return orders
