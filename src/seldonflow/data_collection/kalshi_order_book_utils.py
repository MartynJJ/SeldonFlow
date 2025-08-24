from seldonflow.util import custom_methods, custom_types


import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional

_COLUMN_RANGE = np.arange(1, 100, dtype=np.int32)
_EXTRA_COLS = [
    "TOP_YES_BID_PRICE",
    "TOP_YES_BID_SIZE",
    "TOP_YES_ASK_PRICE",
    "TOP_YES_ASK_SIZE",
]
_FULL_COLS = list(_COLUMN_RANGE) + _EXTRA_COLS


def create_orderbook_dataframe(
    timestamp: custom_types.TimeStamp, orderbook_data: Dict
) -> pd.DataFrame:
    """
    Raises:
        KeyError: If 'orderbook' key is missing
        ValueError: If indices are out of bounds
    """
    orderbook = orderbook_data["orderbook"]
    data = np.zeros(99, dtype=np.int32)
    extra_arr = np.zeros(4, dtype=np.int32)

    def process_data(data_array, sign: int, extra_idx: List[int]):
        if not data_array:
            if sign == 1:
                np.add.at(extra_arr, extra_idx, [0, 0])
            else:
                np.add.at(extra_arr, extra_idx, [100, 0])
            return

        arr = np.asarray(data_array, dtype=np.int32)
        if sign == 1:
            indices = arr[:, 0] - 1
        else:
            indices = 99 - arr[:, 0]
        values = arr[:, 1] * sign
        extra_arr_sub = np.array([indices[-1] + 1, values[-1]], dtype=np.int32)
        if np.any((indices < 0) | (indices >= 99)):
            raise ValueError("Orderbook indices must be between 1 and 99")
        np.add.at(extra_arr, extra_idx, extra_arr_sub)
        np.add.at(data, indices, values)

    process_data(orderbook.get("yes"), 1, [0, 1])
    process_data(orderbook.get("no"), -1, [2, 3])
    df = pd.DataFrame(
        np.append(data, extra_arr).reshape(1, -1),
        columns=_FULL_COLS,
        index=[timestamp],
    )
    df.index.name = "timestamp"
    return df
