from seldonflow.util import custom_types
import datetime
import pytz
from typing import Optional
import pandas as pd

_COMPASS_TO_DEGREES = {
    "N": 0.0,
    "NNE": 22.5,
    "NE": 45.0,
    "ENE": 67.5,
    "E": 90.0,
    "ESE": 112.5,
    "SE": 135.0,
    "SSE": 157.5,
    "S": 180.0,
    "SSW": 202.5,
    "SW": 225.0,
    "WSW": 247.5,
    "W": 270.0,
    "WNW": 292.5,
    "NW": 315.0,
    "NNW": 337.5,
}


def get_degress_from_direction(direction: str) -> Optional[float]:
    return _COMPASS_TO_DEGREES.get(direction)


def time_stamp_to_NYC(time_stamp: custom_types.TimeStamp):
    return datetime.datetime.fromtimestamp(
        time_stamp, tz=pytz.timezone("America/New_York")
    )


def time_stamp_to_NYC_str(time_stamp: custom_types.TimeStamp):
    return datetime.datetime.fromtimestamp(
        time_stamp, tz=pytz.timezone("America/New_York")
    ).strftime("%Y-%m-%d %H:%M:%S %Z")


def is_valid_dataframe(df: Optional[pd.DataFrame]) -> bool:
    return df is not None and not df.empty
