from seldonflow.util import custom_types

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import time


class ExecutionOrder(ABC):
    _order_id_counter = 0
    _order_id: str
    _ticker: str
    _market_side: custom_types.MarketSide
    _side: custom_types.Side
    _count: int
    _order_type: custom_types.OrderType
    _price: Optional[custom_types.Price]
    _venue: custom_types.Venue

    def __init__(
        self,
        venue: custom_types.Venue,
        ticker: str,
        market_side: custom_types.MarketSide,
        side: custom_types.Side,
        count: int,
        order_type: custom_types.OrderType,
        price: Optional[custom_types.Price] = None,
    ):

        self._ticker = ticker
        self._market_side = market_side
        self._side = side
        self._count = count
        self._order_type = order_type
        self._price = price
        self._venue = venue
        self._order_id_count = self._order_id_counter
        self._order_id = f"{str(int(time.time()))[2:]}_{self._order_id_count:07d}"
        ExecutionOrder._order_id_counter += 1
        if order_type == custom_types.OrderType.LIMIT and not price:
            raise ValueError("Limit orders require either yes_price or no_price")

    def cent_price(self) -> Optional[int]:
        if self._price:
            return int(self._price * 100)
        else:
            return None

    def yes_cent_price(self) -> Optional[int]:
        assert self._market_side != custom_types.MarketSide.INVALID
        if self._market_side == custom_types.MarketSide.YES:
            return self.cent_price()
        else:
            return None

    def no_cent_price(self) -> Optional[int]:
        assert self._market_side != custom_types.MarketSide.INVALID
        if self._market_side == custom_types.MarketSide.NO:
            return self.cent_price()
        else:
            return None

    @abstractmethod
    def to_payload(self) -> Dict[str, Any]:
        pass

    def venue(self) -> custom_types.Venue:
        return self._venue

    def __repr__(self) -> str:
        return f"ExecutionOrder(venue={self._venue}, ticker={self._ticker}, market_side={self._market_side}, side={self._side}, count={self._count}, order_type={self._order_type}, price={self._price})"


class KalshiOrder(ExecutionOrder):
    def __init__(
        self,
        ticker: str,
        market_side: custom_types.MarketSide,
        side: custom_types.Side,
        count: int,
        order_type: custom_types.OrderType,
        price: Optional[custom_types.Price] = None,
        time_in_force: Optional[custom_types.TimeInForce] = None,
        expiration_ts: Optional[int] = None,
    ):
        super().__init__(
            custom_types.Venue.KALSHI,
            ticker,
            market_side,
            side,
            count,
            order_type,
            price,
        )
        self._time_in_force = time_in_force
        self._expiration_ts = expiration_ts
        assert self._time_in_force in custom_types.KALSHI_TIME_IN_FORCE

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "ticker": self._ticker,
            "client_order_id": self._order_id,
            "side": self._market_side.value.lower(),
            "action": self._side.value.lower(),
            "count": self._count,
            "type": self._order_type.value.lower(),
        }

        optional_params = {
            "yes_price": self.yes_cent_price(),
            "no_price": self.no_cent_price(),
            "time_in_force": (
                self._time_in_force.value.lower() if self._time_in_force else None
            ),
            "expiration_ts": self._expiration_ts,
            "sell_position_floor": None,
            "buy_max_cost": None,
            "close_cancel_count": None,
            "source": None,
        }
        for key, value in optional_params.items():
            if value is not None:
                payload[key] = value

        return payload

    def __repr__(self) -> str:
        return (
            f"KalshiOrder(ticker={self._ticker}, market_side={self._market_side}, "
            f"side={self._side}, count={self._count}, order_type={self._order_type}, "
            f"price={self._price}, time_in_force={self._time_in_force}, "
            f"expiration_ts={self._expiration_ts})"
        )
