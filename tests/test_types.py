import pytest
from typing import NewType
from seldonflow.util.types import Temp, TempC, TempF


@pytest.fixture
def temp_c_25():
    """Fixture for TempC(25.0)."""
    return TempC(25.0)


@pytest.fixture
def temp_f_77():
    """Fixture for TempF(77.0)."""
    return TempF(77.0)


def test_init_with_temp_c(temp_c_25):
    """Test initialization with TempC and unit='C'."""
    temp = Temp(temp_c_25)
    assert temp.as_celsius() == TempC(25.0)
    assert temp.as_fahrenheit() == TempF(77.0)  # 25.0 * 9/5 + 32 = 77.0


def test_init_with_temp_f(temp_f_77):
    """Test initialization with TempF and unit='F'."""
    temp = Temp.from_f(temp_f_77)
    assert temp.as_celsius() == TempC(25.0)  # (77.0 - 32) * 5/9 = 25.0
    assert temp.as_fahrenheit() == TempF(77.0)
