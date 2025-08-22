import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock
from seldonflow.data_collection.kalshi_order_book_utils import (
    create_orderbook_dataframe,
)
from seldonflow.util import custom_types

# Mock custom_types.TimeStamp as float
custom_types = Mock()
custom_types.TimeStamp = float


@pytest.fixture
def valid_orderbook_data():
    return {
        "orderbook": {"yes": [[1, 100], [2, 200], [99, 300]], "no": [[1, 50], [3, 150]]}
    }


@pytest.fixture
def empty_orderbook_data():
    return {"orderbook": {"yes": [], "no": []}}


@pytest.fixture
def invalid_indices_data():
    return {
        "orderbook": {
            "yes": [[0, 100], [100, 200]],  # Invalid indices: 0, 100
            "no": [[1, 50]],
        }
    }


def test_valid_orderbook_dataframe(valid_orderbook_data):
    timestamp = custom_types.TimeStamp(1234567890.0)
    df = create_orderbook_dataframe(timestamp, valid_orderbook_data)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 99)
    assert df.index[0] == timestamp
    assert df.columns.tolist() == list(range(1, 100))
    assert df.iloc[0, 0] == 50  # 100 - 50 at index 1
    assert df.iloc[0, 1] == 200  # 200 at index 2
    assert df.iloc[0, 2] == -150  # -150 at index 3
    assert df.iloc[0, 98] == 300  # 300 at index 99


def test_empty_orderbook_dataframe(empty_orderbook_data):
    timestamp = custom_types.TimeStamp(1234567890.0)
    df = create_orderbook_dataframe(timestamp, empty_orderbook_data)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 99)
    assert df.index[0] == timestamp
    assert (df.iloc[0] == 0).all()  # All zeros for empty data


def test_missing_orderbook_key():
    timestamp = custom_types.TimeStamp(1234567890.0)
    with pytest.raises(KeyError):
        create_orderbook_dataframe(timestamp, {})


def test_invalid_indices(invalid_indices_data):
    timestamp = custom_types.TimeStamp(1234567890.0)
    with pytest.raises(ValueError, match="Orderbook indices must be between 1 and 99"):
        create_orderbook_dataframe(timestamp, invalid_indices_data)


def test_none_values_in_orderbook():
    timestamp = custom_types.TimeStamp(1234567890.0)
    orderbook_data = {"orderbook": {"yes": None, "no": None}}
    df = create_orderbook_dataframe(timestamp, orderbook_data)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 99)
    assert (df.iloc[0] == 0).all()  # All zeros when None
