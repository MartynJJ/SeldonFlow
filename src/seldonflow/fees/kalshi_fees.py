# fees = round up(0.07 x C x P x (1-P))
# P = the price of a contract in dollars (50 cents is 0.5)
# C = the number of contracts being traded
# round up = rounds to the next cent
from math import ceil


def calculate_fee(price_in_dollars: float, number_of_contracts: int) -> float:
    # avoid floating-point issues
    price_cents = int(price_in_dollars * 100)
    fee_hundredths = 7 * number_of_contracts * price_cents * (100 - price_cents)
    return ceil(fee_hundredths / 10000) / 100
