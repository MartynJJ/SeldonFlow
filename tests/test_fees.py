from seldonflow.fees import kalshi_fees

import pytest

TOL = 1e-6


def test_init_kalshi_fees():
    # egs from fee schedule:
    assert 0.01 == pytest.approx(kalshi_fees.calculate_fee(0.01, 1), TOL)
    assert 0.07 == pytest.approx(kalshi_fees.calculate_fee(0.01, 100), TOL)
    assert 0.01 == pytest.approx(kalshi_fees.calculate_fee(0.05, 1), TOL)
    assert 0.34 == pytest.approx(kalshi_fees.calculate_fee(0.05, 100), TOL)
    assert 0.02 == pytest.approx(kalshi_fees.calculate_fee(0.35, 1), TOL)
    assert 1.60 == pytest.approx(kalshi_fees.calculate_fee(0.35, 100), TOL)
    assert 0.02 == pytest.approx(kalshi_fees.calculate_fee(0.50, 1), TOL)
    assert 1.75 == pytest.approx(kalshi_fees.calculate_fee(0.50, 100), TOL)
    assert 0.01 == pytest.approx(kalshi_fees.calculate_fee(0.90, 1), TOL)
    assert 0.63 == pytest.approx(kalshi_fees.calculate_fee(0.90, 100), TOL)
    assert 0.01 == pytest.approx(kalshi_fees.calculate_fee(0.99, 1), TOL)
    assert 0.07 == pytest.approx(kalshi_fees.calculate_fee(0.99, 100), TOL)
