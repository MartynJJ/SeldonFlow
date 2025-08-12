from seldonflow.api_client.order import (
    ExecutionOrder,
    ExecutionOrderDestination,
    KalshiOrder,
)
from seldonflow.util.config import Config
from seldonflow.util import custom_types
from seldonflow.api_client.api_client import iApiClient, ApiMethod

import kalshi
from datetime import date, datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa, types
from cryptography.exceptions import InvalidSignature
from pathlib import Path
from enum import Enum
import requests
from typing import Optional, Literal
import time


class KalshiEndPoint(Enum):
    Invalid = ""
    Balance = "/trade-api/v2/portfolio/balance"
    Orders = "/trade-api/v2/portfolio/orders"


class KalshiSubClient:
    _public_key: str
    _private_key_path: Path
    _private_key: types.PrivateKeyTypes
    _base_url: str = "https://api.elections.kalshi.com"

    def __init__(self, public_key: str, private_key_path: Path):
        self._public_key = public_key
        self._private_key_path = private_key_path
        self._private_key = self.load_private_key_from_file(private_key_path)

    def _generate_msg_string(
        self,
        api_method: ApiMethod,
        kalshi_end_point: KalshiEndPoint,
        timestamp_str: str,
    ):
        assert api_method != ApiMethod.Invalid
        assert kalshi_end_point != KalshiEndPoint.Invalid
        return self._generate_msg_string_helper(
            api_method.value, kalshi_end_point.value, timestamp_str
        )

    def _generate_msg_string_helper(
        self, api_method: str, path: str, timestamp_str: str
    ):
        return timestamp_str + api_method + path

    def _generate_signature(self, msg_string: str):
        return self.sign_pss_text(self._private_key, msg_string)

    def _generate_headers(
        self, api_method: ApiMethod, kalshi_end_point: KalshiEndPoint
    ) -> dict:
        timestamp_str = str(int(datetime.now().timestamp() * 1000))
        msg_string = self._generate_msg_string(
            api_method=api_method,
            kalshi_end_point=kalshi_end_point,
            timestamp_str=timestamp_str,
        )
        return {
            "KALSHI-ACCESS-KEY": "2f92cc1c-739b-4d94-a1c5-0b38f6e306b0",
            "KALSHI-ACCESS-SIGNATURE": self._generate_signature(msg_string=msg_string),
            "KALSHI-ACCESS-TIMESTAMP": timestamp_str,
        }

    def request_get(self, api_endpoint: KalshiEndPoint):
        headers = self._generate_headers(
            api_method=ApiMethod.Get, kalshi_end_point=api_endpoint
        )
        return requests.get(self._base_url + api_endpoint.value, headers=headers)

    def get(self, api_endpoint: KalshiEndPoint):
        return self.request_get(api_endpoint=api_endpoint).json()

    def request_post(self, api_endpoint: KalshiEndPoint, data: dict):
        headers = self._generate_headers(
            api_method=ApiMethod.Post, kalshi_end_point=api_endpoint
        )
        headers["Content-Type"] = "application/json"

        return requests.post(
            self._base_url + api_endpoint.value, json=data, headers=headers
        )

    @staticmethod
    def load_private_key_from_file(file_path: Path) -> types.PrivateKeyTypes:
        if not file_path.is_file():
            raise FileNotFoundError(f"Private key file not found: {file_path}")

        try:
            with file_path.open("rb") as key_file:
                key_data = key_file.read()
                if not key_data:
                    raise ValueError("Private key file is empty")
                return serialization.load_pem_private_key(
                    key_data,
                    password=None,
                    backend=default_backend(),
                )
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to load private key: {str(e)}") from e

    @staticmethod
    def sign_pss_text(private_key: rsa.RSAPrivateKey, text: str) -> str:
        message = text.encode("utf-8")
        try:
            signature = private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH,
                ),
                hashes.SHA256(),
            )
            return base64.b64encode(signature).decode("utf-8")
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

    @staticmethod
    def create_order(
        ticker: str,
        client_order_id: str,
        side: Literal["yes", "no"],
        action: Literal["buy", "sell"],
        count: int,
        type: Literal["market", "limit"] = "market",
        yes_price: Optional[int] = None,
        no_price: Optional[int] = None,
        time_in_force: Optional[Literal["ioc", "fok", "gtc", "gtd"]] = None,
        expiration_ts: Optional[int] = None,
        sell_position_floor: Optional[int] = None,
        buy_max_cost: Optional[int] = None,
        close_cancel_count: Optional[int] = None,
        source: Optional[str] = None,
        auto_expiration_hours: Optional[int] = None,
    ) -> dict:
        if type == "limit" and not (yes_price or no_price):
            raise ValueError("Limit orders require either yes_price or no_price")

        if side == "yes" and no_price:
            raise ValueError("Cannot set no_price when side is 'yes'")

        if side == "no" and yes_price:
            raise ValueError("Cannot set yes_price when side is 'no'")

        if time_in_force == "gtd" and not expiration_ts and not auto_expiration_hours:
            raise ValueError(
                "GTD orders require expiration_ts or auto_expiration_hours"
            )

        if yes_price and (yes_price < 1 or yes_price > 99):
            raise ValueError("yes_price must be between 1 and 99 cents")

        if no_price and (no_price < 1 or no_price > 99):
            raise ValueError("no_price must be between 1 and 99 cents")

        if auto_expiration_hours and not expiration_ts:
            expiration_ts = int(time.time()) + (auto_expiration_hours * 3600)

        payload = {
            "ticker": ticker,
            "client_order_id": client_order_id,
            "side": side,
            "action": action,
            "count": count,
            "type": type,
        }

        optional_params = {
            "yes_price": yes_price,
            "no_price": no_price,
            "time_in_force": time_in_force,
            "expiration_ts": expiration_ts,
            "sell_position_floor": sell_position_floor,
            "buy_max_cost": buy_max_cost,
            "close_cancel_count": close_cancel_count,
            "source": source,
        }

        for key, value in optional_params.items():
            if value is not None:
                payload[key] = value

        return payload


class KalshiClient(iApiClient):
    def __init__(self, config: Config):
        super().__init__(config)
        self.public_key_id = self._api_keys["public_key_id"]
        self.private_key_path = self._api_keys["private_key_path"]
        self._sub_client = KalshiSubClient(
            self.public_key_id, Path(self.private_key_path)
        )

        kalshi.auth.set_key(
            access_key=self.public_key_id,
            private_key_path=self.private_key_path,
        )
        self.api = kalshi.rest

    def get_api_keys_from_config(self, config: Config) -> dict:
        return config.get_api_key("kalshi")

    def get_market_data(self, market_id: str) -> dict:
        """Fetch the orderbook for a given market ID."""
        return self.api.market.GetMarket(market_id)

    def get_market_orderbook(self, market_id: str) -> dict:
        """Fetch the orderbook for a given market ID."""
        return self.api.market.GetMarketOrderbook(market_id)

    def get_balances(self) -> dict:
        balance = self.api.portfolio.GetBalance()
        return {"USD": balance["balance"] / 100}

    def get_positions(self) -> dict:
        positions_raw = self.api.portfolio.GetPositions()
        return self.format_kalshi_positions(positions_raw=positions_raw)

    def format_kalshi_positions(self, positions_raw: dict):
        positions = positions_raw.get("market_positions", [])
        return positions

    def get_event(self, base_ticker: str, event_date: date):
        event_ticker = f"{base_ticker}-{event_date.strftime('%y%b%d').upper()}"
        return self.api.market.GetEvent(event_ticker=event_ticker)

    @staticmethod
    def dollar_to_cents(price: custom_types.Price):
        return int(price * 100.0)

    def send_order(self, execution_order: ExecutionOrder) -> dict:
        assert execution_order.destination() == ExecutionOrderDestination.Kalshi
        response = {}
        print(execution_order)
        if execution_order.get_market_side() == custom_types.MarketSide.NO:
            response = self.api.portfolio.CreateOrder(
                action=execution_order.side_to_str().lower(),
                client_order_id=execution_order.client_order_id(),
                count=execution_order.get_size(),
                no_price=self.dollar_to_cents(execution_order.get_price()),
                side=execution_order.get_market_side().value.lower(),
                ticker=execution_order.get_ticker(),
                type=execution_order.get_order_type().value.lower(),
            )
        return response
