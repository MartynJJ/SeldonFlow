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

from datetime import date
from typing import List, Dict, Any, Tuple


class TROS(iStrategy):
    _active_tickers: list[TempTickerEvent] = []
    _max_notional_cents = 1000

    def __init__(self, params: StrategyParams, api_client: iApiClient, today: date):
        super().__init__(params)
        self._api_client = api_client
        self._location = self.get_location_from_params(params)
        self._base_ticker = KALSHI_MAX_TEMP_LOCATION_TO_TICKER.get(self._location, "")
        self._event_info = {}
        self._max_observed = Temp.from_f(TempF(0.0))
        self._today = today

    @staticmethod
    def get_location_from_params(params):
        return TempLocation.from_string(
            params.get_params().get("Market", {}).get("location", "")
        )

    def on_tick(self, time_stamp: TimeStamp) -> ActionRequest:
        self.set_max_observed_temperature(time_stamp)
        execution_list = self.generate_execution_list()
        executions = []
        for possible_execution in execution_list:
            if possible_execution.get("net_winnings", -1) > 0:
                try:
                    executions.append(possible_execution["exeuction_order"])
                except KeyError as key_error:
                    print(f"Key Error: {key_error}")

        return ActionRequest([], executions=executions)

    def get_max_observed_temperature(self, time_stamp: TimeStamp) -> Temp:
        return Temp.from_f(TempF(0.0))

    def set_max_observed_temperature(self, time_stamp: TimeStamp) -> None:
        self._max_observed = self.get_max_observed_temperature(time_stamp)

    def get_all_active_tickers(self):
        self._event_info = self._api_client.get_event(self._base_ticker, self._today)
        markets = self._event_info.get("markets", [])
        for market in markets:
            self._active_tickers.append(TempTickerEvent(market))

    def get_resting_orders(self, ticker):
        return self._api_client.get_market_orderbook(ticker)

    def get_active_markets_below_current_max(self):
        tickers = []
        for ticker in self._active_tickers:
            if ticker.cap_strike.as_fahrenheit() < self._max_observed.as_fahrenheit():
                tickers.append(ticker)
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
