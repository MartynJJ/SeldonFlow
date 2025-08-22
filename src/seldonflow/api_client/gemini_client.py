from seldonflow.api_client import trading_api_client
from seldonflow.util.config import Config

from typing import Dict, Any, List, Optional
import json
import base64
import hmac
import hashlib
import time
from pathlib import Path
import datetime
from enum import Enum
import requests

GEMINI_V1 = "https://api.gemini.com/v1/"
GEMINI_V2 = "https://api.gemini.com/v2/"


class GEMINI_ENDPOINT(Enum):
    Invalid = ""
    GetTickerV1 = GEMINI_V1 + "pubticker/"
    GetTickerV2 = GEMINI_V2 + "ticker/"
    CancelAllOrders = GEMINI_V1 + "order/cancel/all"


class GeminiClient(trading_api_client.iTradingClient):
    def __init__(
        self, config: Config, trading_access: trading_api_client.TradingAccess
    ):
        super().__init__(config=config, access=trading_access)
        self._account: List[str] = ["primary"]

    def get_api_keys_from_config(self, config: Config) -> Dict[str, Any]:
        keypair = config.api_keys().get("gemini")
        if keypair:
            return keypair
        else:
            raise KeyError(f"Missing KeyPair For Gemini")

    def _secret(self):
        return self._api_keys["api_secret"].encode()

    def _key(self):
        return self._api_keys["api_key"]

    def get_ticker_v1(self, ticker: str):
        return self._get(GEMINI_ENDPOINT.GetTickerV1, ticker)

    def get_ticker_v2(self, ticker: str):
        return self._get(GEMINI_ENDPOINT.GetTickerV2, ticker)

    def _get(self, end_point: GEMINI_ENDPOINT, additional: str):
        url = end_point.value + additional
        response = requests.get(url, headers=self._generate_header(url=url))
        return response.json()

    def _post(
        self,
        end_point: GEMINI_ENDPOINT,
        additional: str = "",
        payload: Dict[str, Any] = {},
        data: Optional[Dict[str, Any]] = None,
    ):
        url = end_point.value + additional
        response = requests.post(
            url=url, data=data, headers=self._generate_header(url, payload=payload)
        )
        return response

    @staticmethod
    def generate_nonce():
        return str(int(time.time() * 1000))

    def _generate_header(self, url: str, payload={}):
        payload_nonce = self.generate_nonce()
        _, path = url.split(".com")
        payload["request"] = path
        payload["nonce"] = payload_nonce
        encoded_payload = json.dumps(payload).encode()
        b64 = base64.b64encode(encoded_payload)
        signature = hmac.new(self._secret(), b64, hashlib.sha384).hexdigest()
        return {
            "Content-Type": "application/json",
            "Content-Length": "0",
            "X-GEMINI-APIKEY": self._key(),
            "X-GEMINI-PAYLOAD": b64,
            "X-GEMINI-SIGNATURE": signature,
            "Cache-Control": "no-cache",
        }

    def cancel_all_orders(self) -> Optional[Dict[str, Any]]:
        response = self._post(
            GEMINI_ENDPOINT.CancelAllOrders, payload={"account": self._account}
        )
        status = response.status_code
        json_response = response.json()
        if status == 200:
            try:
                assert json_response.get("result") == "ok"
                return json_response
            except AssertionError as assert_error:
                self.logger.error(f"Assertion Error {assert_error}")
        else:
            self.logger.error(f"Cancel Error: {json_response}")
            return None

    def send_order_helper(self, trading_order: trading_api_client.TradingOrder):
        pass

    def get_positions(self) -> dict:
        return {}

    def get_ticker_info(self, ticker: str):
        pass
