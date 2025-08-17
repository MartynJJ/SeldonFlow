# types.py cannot be used as conflicts with built in types
from enum import Enum
from typing import NewType
import pytz
from datetime import datetime

TimeStamp = NewType("TimeStamp", float)
Seconds = NewType("Seconds", int)
TempC = NewType("TempC", float)
TempF = NewType("TempF", float)
Price = NewType("Price", float)


def time_stamp_to_NYC(time_stamp: TimeStamp):
    return datetime.fromtimestamp(time_stamp, tz=pytz.timezone("America/New_York"))


def time_stamp_to_NYC_str(time_stamp: TimeStamp):
    return datetime.fromtimestamp(
        time_stamp, tz=pytz.timezone("America/New_York")
    ).strftime("%Y-%m-%d %H:%M:%S %Z")


class Temp:
    temp_c: TempC
    temp_f: TempF

    def __init__(self, temp_c: TempC) -> None:
        if isinstance(temp_c, float):
            self._celsius = temp_c
            self._fahrenheit = TempF(self._celsius * 9 / 5 + 32)
        else:
            raise TypeError("Unexpected type for temperature")

    def as_celsius(self) -> TempC:
        return self._celsius

    def as_fahrenheit(self) -> TempF:
        return self._fahrenheit

    @staticmethod
    def from_f(temp_f: TempF):
        return Temp(TempC((temp_f - 32) * 5 / 9))

    def __str__(self) -> str:
        return f"Temperature: {self._celsius}°C / {self._fahrenheit}°F"

    def __repr__(self) -> str:
        return f"Temperature: {self._celsius}°C / {self._fahrenheit}°F"

    def __eq__(self, other):
        if isinstance(other, Temp):
            return self._celsius == other._celsius
        return False

    def __lt__(self, other):
        if isinstance(other, Temp):
            return self._celsius < other._celsius
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Temp):
            return self._celsius <= other._celsius
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Temp):
            return self._celsius > other._celsius
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Temp):
            return self._celsius >= other._celsius
        return NotImplemented


class Side(Enum):
    INVALID = "INVALID"
    BUY = "BUY"
    SELL = "SELL"

    from_str = staticmethod(
        lambda s: Side[s.upper()] if s.upper() in Side.__members__ else Side.INVALID
    )

    def to_sign(self):
        if self == Side.BUY:
            return 1
        elif self == Side.SELL:
            return -1
        else:
            return 0


class MarketSide(Enum):
    INVALID = "INVALID"
    YES = "YES"
    NO = "NO"

    from_str = staticmethod(
        lambda s: Side[s.upper()] if s.upper() in Side.__members__ else Side.INVALID
    )


class OrderType(Enum):
    INVALID = "INVALID"
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"

    @staticmethod
    def from_str(s: str):
        try:
            return OrderType[s.upper()]
        except KeyError:
            raise ValueError(f"Invalid order type: {s}")


class TimeInForce(Enum):
    INVALID = "INVALID"
    IOC = "IOC"
    FOC = "FOC"
    GTC = "GTC"
    GTD = "GTD"


KALSHI_TIME_IN_FORCE = set([TimeInForce.IOC, TimeInForce.FOC, TimeInForce.GTC, None])


class Venue(Enum):
    INVALID = "INVALID"
    KALSHI = "KALSHI"
    POLYMARKET = "POLYMARKET"


def main():
    time_stamp = TimeStamp(100.1)
    seconds = Seconds(1)
    temp_c = TempC(100.0)
    temp_f = TempF(100.0)


if __name__ == "__main__":
    main()
