import jwt
from cryptography.hazmat.primitives import serialization
import time
import secrets

from trading.trading_client import TradingClient


class CoinbaseClient(TradingClient):
    HOST = "api.coinbase.com"

    def __init__(self, api_key: str, api_secret_key: str, base_url: str):
        self.headers = { 
            'Content-Type': 'application/json'
        }
        super().__init__(self.headers)

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


class CoinbaseTradingClient(CoinbaseClient):
    def __init__(self, api_key: str, api_secret_key: str, base_url: str):
        super().__init__(api_key, api_secret_key, base_url)

    def get_headers(self, method: str, path: str):
        uri = f"{method} {self.HOST}/{path}"
        headers = self.headers
        headers['Authorization'] = f"Bearer {self.build_jwt(uri)}"
        return headers

    def list_orders(self):
        # GET /orders/historical/batch
        path = "api/v3/brokerage/orders/historical/batch"
        return self.get(f"{self.base_url}{path}", self.get_headers("GET", path))

    def list_accounts(self):
        # GET /brokerage/accounts
        path = "api/v3/brokerage/accounts"
        return self.get(f"{self.base_url}{path}", self.get_headers("GET", path))

    def create_orders(self):
        # POST /orders
        pass
    
    def get_order(self, order_id):
        # GET /orders/historical/{order_id}
        path = f"api/v3/orders/historical/{order_id}"
        return self.get(f"{self.base_url}{path}", self.get_headers("GET", path))

    def preview_order(self):
        # POST /orders/preview
        pass