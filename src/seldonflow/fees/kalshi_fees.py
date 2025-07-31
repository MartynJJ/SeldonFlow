# fees = round up(0.07 x C x P x (1-P))
# P = the price of a contract in dollars (50 cents is 0.5)
# C = the number of contracts being traded
# round up = rounds to the next cent
from math import ceil


def calculate_fee(price_in_dollars: float, number_of_contracts: int):
    fee = 0.7 * number_of_contracts * price_in_dollars * (1 - price_in_dollars)
    rounded_fee = 0.01 * ceil(100 * fee)
    return rounded_fee
