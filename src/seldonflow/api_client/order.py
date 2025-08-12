from seldonflow.util.custom_types import Side, Price, OrderType, MarketSide

from abc import ABC, abstractmethod
from enum import Enum


class ExecutionOrderDestination(Enum):
    Invalid = 0
    Kalshi = 1


class ExecutionOrder(ABC):
    _order_id_counter = 0
    _unique_id: str

    def __init__(self):
        pass

    def _generate_id(self) -> None:
        self._unique_id = f"{self.destination()}_{self._order_id_counter}"
        ExecutionOrder._order_id_counter += 1

    @abstractmethod
    def destination(self) -> ExecutionOrderDestination:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def side_to_str(self) -> str:
        pass

    def client_order_id(self) -> str:
        return self._unique_id

    @abstractmethod
    def get_size(self) -> int:
        pass

    @abstractmethod
    def get_price(self) -> Price:
        pass

    @abstractmethod
    def get_market_side(self) -> MarketSide:
        pass

    @abstractmethod
    def get_ticker(self) -> str:
        pass

    @abstractmethod
    def get_order_type(self) -> OrderType:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


class KalshiOrder(ExecutionOrder):
    side: Side
    market_side: MarketSide
    size: int
    price: Price
    post_only: bool
    ticker: str
    fill_or_kill: bool
    order_type: OrderType
    _destination: ExecutionOrderDestination

    def __init__(
        self,
        side: Side,
        market_side: MarketSide,
        size: int,
        price: Price,
        post_only: bool,
        ticker: str,
        fill_or_kill: bool,
        order_type: OrderType,
    ):
        self._destination = ExecutionOrderDestination.Kalshi
        self.side = side
        self.market_side = market_side
        self.size = size
        self.price = price
        self.post_only = post_only
        self.ticker = ticker
        self.fill_or_kill = fill_or_kill
        self.order_type = order_type
        self._generate_id()
        print(f"Order Created: {self._unique_id}")

    def destination(self) -> ExecutionOrderDestination:
        return self._destination

    def side_to_str(self) -> str:
        assert self.side != Side.INVALID
        return str(self.side.value).lower()

    def to_dict(self) -> dict:
        return {
            "market_id": self.ticker,
            "side": self.side_to_str(),
            "size": self.size,
            "price": self.price,
            "post_only": self.post_only,
            "fill_or_kill": self.fill_or_kill,
            "order_type": str(self.order_type).lower(),
        }

    def get_size(self) -> int:
        return self.size

    def get_price(self) -> Price:
        return self.price

    def get_market_side(self) -> MarketSide:
        return self.market_side

    def get_ticker(self) -> str:
        return self.ticker

    def get_order_type(self) -> OrderType:
        return self.order_type

    def __repr__(self) -> str:
        return f"KalshiOrder(ID: {self._unique_id}, Side: {self.side}, MarketSide: {self.market_side}, Size: {self.size}, Price: {self.price}, PostOnly: {self.post_only}, Ticker: {self.ticker}, FillOrKill: {self.fill_or_kill}, OrderType: {self.order_type})"
