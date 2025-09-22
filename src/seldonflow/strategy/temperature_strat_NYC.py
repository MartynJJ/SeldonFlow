from seldonflow.util import custom_types, custom_methods, ticker_mapper, tick_manager
from seldonflow.strategy import i_strategy
from seldonflow.api_client.api_client import iApiClient
from seldonflow.api_client.order import KalshiOrder
from seldonflow.fees import kalshi_fees
from seldonflow.data_collection.data_manager import DataCollector, DataManager
from seldonflow.data_collection import intraday_nws_util
from seldonflow.util.strategy_utils import NYC_6hr_max_utils

from datetime import date, time, datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import math
from dataclasses import dataclass
import re
import asyncio

START_TIME_HOUR = 13
END_TIME_HOUR = 14
BUY_PEAK_UNCERTAINTY = 0.3


class MaxTempNYCStrategy(i_strategy.iStrategy):
    _active_tickers: list[ticker_mapper.TempTickerEvent] = []
    _loaded: bool = False
    _nws_site_code: str = "knyc"
    _today: date
    _current_year: int
    _max_notional_cents = 2000
    _buy_peak_uncerntainty: float = BUY_PEAK_UNCERTAINTY

    def __init__(
        self,
        params: i_strategy.StrategyParams,
        api_client: iApiClient,
        today: date,
        data_manager: DataManager,
    ):
        super().__init__(params)

        self._tick_manager = tick_manager.TickManager(
            tick_interval=custom_types.TimeStamp(params.tick_interval()),
            time_window=self.get_time_window(),
            name="MaxTempNYCStrategy",
        )
        self._location = self.get_location_from_params(params)
        self._base_ticker = ticker_mapper.KALSHI_MAX_TEMP_LOCATION_TO_TICKER.get(
            self._location, ""
        )
        self._today = today
        self._current_year = today.year
        self._api_client = api_client
        self.logger.info(f"MaxTempNYCStrategy Loaded: {self}")
        # assert False

    def __repr__(self) -> str:
        return f"MaxTempNYCStrategy(location={self._location}, base_ticker={self._base_ticker})"

    def update_for_new_day(self):
        new_day = custom_methods.time_stamp_to_NYC(
            self._tick_manager._next_tick_update
        ).date()

        self.logger.info(
            f"Updating for new day. Current Day: {self._today.strftime('%Y-%m-%d')} New Day: {new_day.strftime('%Y-%m-%d')}"
        )
        self._today = new_day
        self._current_year = self._today.year
        self.initial_load()

    def initial_load(self):
        self.get_all_todays_active_tickers()
        self._loaded = True

    def get_all_todays_active_tickers(self):
        self._active_tickers.clear()
        self._event_info = self._api_client.get_event(self._base_ticker, self._today)
        markets = self._event_info.get("markets", [])
        for market in markets:
            self._active_tickers.append(ticker_mapper.TempTickerEvent(market))
        self.logger.info(f"Active Tickers: {self._active_tickers}")

    @staticmethod
    def get_location_from_params(params):
        return ticker_mapper.TempLocation.from_string(
            params.get_params().get("Market", {}).get("location", "")
        )

    def get_time_window(self) -> custom_types.TimeWindow:
        return custom_types.TimeWindow(
            start_time=time(hour=START_TIME_HOUR), end_time=time(hour=END_TIME_HOUR)
        )

    def set_next_tick_time(self, next_tick_time: custom_types.TimeStamp):
        assert False
        pass

    def TICK_INTERVAL_SECONDS(self) -> custom_types.TimeStamp:
        return self._tick_manager._tick_interval

    def on_tick(
        self, current_time: custom_types.TimeStamp
    ) -> Optional[i_strategy.ActionRequest]:
        if self._tick_manager.ready_with_auto_update(current_time=current_time):
            if not self._loaded:
                self.initial_load()

            execution_list = self.check_for_6hr_max(self._current_year)
            executions = []
            for possible_execution in execution_list:
                if possible_execution.get("i", -1) > 0:
                    try:
                        executions.append(possible_execution["exeuction_order"])
                    except KeyError as key_error:
                        print(f"Key Error: {key_error}")
            return i_strategy.ActionRequest([], executions=executions)

    def check_for_6hr_max(self, current_year: int) -> List[Dict[str, Any]]:
        orders = []
        try:
            six_hour_max_temps = NYC_6hr_max_utils.aggro_get_latest_print(
                self._nws_site_code, current_year
            )
            if six_hour_max_temps == None:
                return []
            six_max_hour_temp = six_hour_max_temps.six_hour_max_temp
            orders.append(self.generate_execution_list_below_temp(six_max_hour_temp))
            if six_max_hour_temp > six_hour_max_temps.print_temp:
                self.logger.warning(
                    f"Entering BUY THE PEAK strat: 6 hour max = {six_max_hour_temp}, recent print = {six_hour_max_temps.print_temp}"
                )
                orders.append(self.buy_the_peak(six_max_hour_temp))
        except Exception as e:
            self.logger.error(f"Error Caught in check_for_6hr_max: {e}")
        return orders

    def get_ticker_that_contains_temp(
        self, temp: custom_types.Temp
    ) -> Optional[ticker_mapper.TempTickerEvent]:
        contains_tickers = []
        for ticker in self._active_tickers:
            if ticker.contains(temp):
                contains_tickers.append(ticker)
        if len(contains_tickers) == 1:
            return contains_tickers[0]
        else:
            self.logger.error(
                f"Multiple tickers contain single temp: tickers={contains_tickers}, temp={temp}"
            )
            return None

    def buy_the_peak(self, peak: custom_types.Temp) -> List[Dict[str, Any]]:
        ticker = self.get_ticker_that_contains_temp(peak)
        if ticker == None:
            return []
        order_book_no = self.get_no_resting_orders_at_temp(peak)
        orders: List[Dict[str, Any]] = []
        if len(order_book_no) == 0:
            return []
        for no_price_cents, size in order_book_no:
            no_price_dollars = no_price_cents * 0.01
            yes_price_dollars = 1.0 - no_price_dollars

            winnings_for_yes = (yes_price_dollars - self._buy_peak_uncerntainty) * size
            fees = kalshi_fees.calculate_fee(yes_price_dollars, size)
            notional = size * yes_price_dollars * 100
            size = (
                size
                if notional <= self._max_notional_cents
                else int(self._max_notional_cents / (100 * yes_price_dollars))
            )
            net_winnings = winnings_for_yes - fees
            if net_winnings > 0:
                orders.append(
                    {
                        "net_winnings": net_winnings,
                        "exeuction_order": KalshiOrder(
                            ticker=ticker.ticker,
                            market_side=custom_types.MarketSide.YES,
                            side=custom_types.Side.BUY,
                            count=size,
                            order_type=custom_types.OrderType.LIMIT,
                            price=custom_types.Price(yes_price_dollars),
                        ),
                    }
                )
        return orders

    def get_no_resting_orders_at_temp(self, temp: custom_types.Temp) -> List[List[int]]:
        ticker = self.get_ticker_that_contains_temp(temp)
        if ticker == None:
            return []
        orderbook = self._api_client.get_market_orderbook(ticker.ticker).get(
            "orderbook", {}
        )
        return orderbook.get("no", [])

    def get_markets_below_temp(self, temp: custom_types.Temp):
        tickers = []
        for ticker in self._active_tickers:
            if ticker.cap_strike.as_fahrenheit() < temp.as_fahrenheit():
                tickers.append(ticker)
        self.logger.info(f"Tickers Below Current Max: {tickers}")
        return tickers

    def get_yes_resting_orders_below_temp(self, temp: custom_types.Temp):
        tickers = self.get_markets_below_temp(temp)
        opportunities = {}
        for ticker in tickers:
            orderbook = self._api_client.get_market_orderbook(ticker.ticker).get(
                "orderbook", {}
            )
            yes_orders = orderbook.get("yes", {})
            opportunities[ticker] = yes_orders
        self.logger.info(f"Resting Order Opportunities: {opportunities}")
        return opportunities

    def generate_execution_list_below_temp(
        self, temp: custom_types.Temp
    ) -> List[Dict[str, Any]]:
        opportunities = self.get_yes_resting_orders_below_temp(temp)
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
                                market_side=custom_types.MarketSide.NO,
                                side=custom_types.Side.BUY,
                                count=size,
                                order_type=custom_types.OrderType.LIMIT,
                                price=custom_types.Price(no_price_dollars),
                            ),
                        }
                    )
        return orders
