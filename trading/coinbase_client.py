import jwt
from urllib.parse import urlencode
from cryptography.hazmat.primitives import serialization
import time
import secrets

from data.data_client import DataClient
from common.helper import Notifier
from trading.trading_client import TradingClient


class CoinbaseTradingClient(TradingClient):
    HOST = "api.coinbase.com"

    def __init__(self, api_key: str, api_secret_key: str, base_url: str, data_client: DataClient, notifier: Notifier=None):
        self.headers = { 
            'Content-Type': 'application/json'
        }
        super().__init__(self.headers, data_client, notifier)

        self.api_key = api_key
        self.api_secret_key = api_secret_key
        self.base_url = base_url

    def build_jwt(self, uri):
        private_key_bytes = self.api_secret_key.encode('utf-8')
        private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
        jwt_payload = {
            'sub': self.api_key,
            'iss': "cdp",
            'nbf': int(time.time()),
            'exp': int(time.time()) + 120,
            'uri': uri,
        }
        jwt_token = jwt.encode(
            jwt_payload,
            private_key,
            algorithm='ES256',
            headers={'kid': self.api_key, 'nonce': secrets.token_hex()},
        )
        return jwt_token

    def get_headers(self, method: str, path: str):
        uri = f"{method} {self.HOST}/{path}"
        headers = self.headers
        headers['Authorization'] = f"Bearer {self.build_jwt(uri)}"
        return headers

    def create_order(self):
        # POST /orders
        return super().create_order()
    
    def process_sell(self):
        return super().process_sell()
    
    def process_buy(self):
        return super().process_buy()
    
    def process_rebuy(self):
        return super().process_rebuy()
    
    def buy(self):
        return super().buy()
    
    def sell(self):
        return super().sell()
    
    def is_runnable(self):
        return super().is_runnable()


    def list_orders(self, filter: dict = None):
        # GET /orders/historical/batch
        # https://api.coinbase.com/api/v3/brokerage/orders/historical/batch
        uri_path = "api/v3/brokerage/orders/historical/batch"
        if filter:
            query_string = urlencode(filter)
            path = f"{uri_path}?{query_string}"
        return self.get(f"{self.base_url}{path}", self.get_headers("GET", uri_path))

    def list_accounts(self):
        # GET /brokerage/accounts
        path = "api/v3/brokerage/accounts"
        return self.get(f"{self.base_url}{path}", self.get_headers("GET", path))
    
    def get_order(self, order_id: str):
        # GET /orders/historical/{order_id}
        path = f"api/v3/orders/historical/{order_id}"
        return self.get(f"{self.base_url}{path}", self.get_headers("GET", path))

    def preview_order(self):
        # POST /orders/preview
        pass

    # data
    def get_latest_bar(self, symbol):
        return True