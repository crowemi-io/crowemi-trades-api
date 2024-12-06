import jwt
from cryptography.hazmat.primitives import serialization
import time
import secrets

from trading.trading_client import TradingClient


class CoinbaseClient(TradingClient):
    def __init__(self, api_key: str, api_secret_key: str, base_url: str):
        self.headers = { 
            'Content-Type': 'application/json'
        }
        super().__init__(self.headers)

        self.api_key = api_key
        self.api_secret_key = api_secret_key
        self.base_url = base_url

        self.build_jwt()


    def build_jwt(self) -> str:
        private_key_bytes = self.api_secret_key.encode('utf-8')
        private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
        jwt_payload = {
            'sub': self.api_key,
            'iss': "cdp",
            'nbf': int(time.time()),
            'exp': int(time.time()) + 120,
            'uri': self.base_url,
        }
        return jwt.encode(
            jwt_payload,
            private_key,
            algorithm='ES256',
            headers={'kid': self.api_key, 'nonce': secrets.token_hex()},
        )


class CoinbaseTradingClient(CoinbaseClient):
    def __init__(self, api_key: str, api_secret_key: str, base_url: str):
        super().__init__(api_key, api_secret_key, base_url)


    def list_account(self):
        jwt = self.build_jwt()
        self.headers['Authorization'] = f"Bearer {self.build_jwt()}"
        url = "v3/brokerage/accounts"
        return self.get(f"{self.base_url}{url}")

