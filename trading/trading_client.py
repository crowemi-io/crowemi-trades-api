from enum import Enum
import json
import requests
from abc import ABCMeta, abstractmethod


class OrderStatus(Enum):
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELED = "CANCELLED"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class TradingClient(metaclass=ABCMeta):
    def __init__ (self, headers): 
        self.headers = headers
        
    def get(self, url, headers=None) -> dict | None:
        hdrs = headers if headers else self.headers
        req = requests.get(url, headers=hdrs)
        if req.status_code == 200:
            return json.loads(req.content)
        else:
            raise Exception(f"Error: {req.content}")
    
    def post(self, url, payload, headers=None) -> dict | None:
        hdrs = headers if headers else self.headers
        req = requests.post(url, json=payload, headers=hdrs)
        if req.status_code == 200:
            return json.loads(req.content)
        else:
            raise Exception(f"Error: {req.content}")

    @abstractmethod
    def create_order(self, payload: dict):
        pass

    @abstractmethod
    def get_order():
        pass

    @abstractmethod
    def process_sell(self):
        pass

    @abstractmethod
    def is_runable(self) -> bool:
        return True

    @abstractmethod
    def get_latest_bar(self, symbol: str):
        pass
