from seldonflow.util import custom_methods, custom_types


import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional

_COLUMN_RANGE = np.arange(1, 100, dtype=np.int32)


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

    def process_data(data_array, sign: int):
        if not data_array:
            return
        arr = np.asarray(data_array, dtype=np.int32)
        indices = arr[:, 0] - 1
        values = arr[:, 1] * sign

        if np.any((indices < 0) | (indices >= 99)):
            raise ValueError("Orderbook indices must be between 1 and 99")

        np.add.at(data, indices, values)

    process_data(orderbook.get("yes"), 1)
    process_data(orderbook.get("no"), -1)

    df = pd.DataFrame(data.reshape(1, -1), columns=_COLUMN_RANGE, index=[timestamp])
    df.index.name = "timestamp"
    return df
