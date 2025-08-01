from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Tuple
from enum import Enum
import math


class TempLocation(Enum):
    INVALID = "INVALID"
    NYC = "NYC"

    @staticmethod
    def from_string(location_str: str):
        if location_str == "NYC":
            return TempLocation.NYC
        return TempLocation.INVALID


KALSHI_TICKER_TO_NAME = {
    "KXHIGHNY": "Highest temperature in NYC today?",
}

KALSHI_MAX_TEMP_TICKER_TO_LOCATION = {
    "KXHIGHNY": TempLocation.NYC,
}


KALSHI_MAX_TEMP_LOCATION_TO_TICKER = {
    TempLocation.NYC: "KXHIGHNY",
    TempLocation.INVALID: "",
}


class MaxTempTicker:
    def __init__(
        self,
        location: TempLocation,
        event_date: date,
        max_temp_range=Tuple[float, float],
    ):
        self._location = location
        self._event_date = event_date
        self._max_temp_range = max_temp_range
        self._event_date_ticker_format = self._event_date.strftime("%y%b%d").upper()
        self._max_temp_range_ticker_format = 0.5 * (
            self._max_temp_range[0] + self._max_temp_range[1]
        )
        self._base_ticker = KALSHI_MAX_TEMP_LOCATION_TO_TICKER.get(self._location, "")

    def get_ticker(self):
        return f"{self._base_ticker}-{self._event_date_ticker_format}-B{self._max_temp_range_ticker_format:.1f}"

    def parse_from_ticker(ticker: str):
        parts = ticker.split("-")
        if len(parts) != 3:
            raise ValueError("Invalid ticker format")

        base_ticker, date_part, range_part = parts
        if base_ticker not in KALSHI_MAX_TEMP_LOCATION_TO_TICKER.values():
            raise ValueError("Invalid base ticker")

        location = KALSHI_MAX_TEMP_TICKER_TO_LOCATION.get(
            base_ticker, TempLocation.INVALID
        )
        event_date = datetime.strptime(date_part, "%y%b%d").date()
        max_temp = float(range_part.split("B")[1])
        max_temp_range = tuple([math.floor(max_temp), math.ceil(max_temp)])
        return MaxTempTicker(location, event_date, max_temp_range)


def main():
    max_temp_ticker = MaxTempTicker(
        TempLocation.NYC, date.fromisoformat("2025-07-28"), tuple([97.0, 98.0])
    )
    print(max_temp_ticker.get_ticker())
    v2 = MaxTempTicker.parse_from_ticker("KXHIGHNY-25JUL28-B97.5")
    print(v2.get_ticker())


if __name__ == "__main__":
    main()
