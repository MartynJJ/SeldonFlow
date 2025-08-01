# import pytest
# from src.seldonflow.api_client.kalshi_client import KalshiClient
# from seldonflow.util.config import Config

# import os


# @pytest.fixture
# def kalshi_client():
#     """Fixture to create a KalshiClient instance."""
#     config = Config()
#     return KalshiClient(config)


# def test_get_market_data(kalshi_client):
#     """Test fetching market data for a financial market."""
#     market_id = "FED-25DEC-T3.00"  # Fed rate market
#     orderbook = kalshi_client.get_market_orderbook(market_id)

#     assert orderbook is not None
#     assert "orderbook" in orderbook
#     assert "yes" in orderbook["orderbook"]
#     assert "no" in orderbook["orderbook"]
