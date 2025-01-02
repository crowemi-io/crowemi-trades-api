from enum import Enum
import json
import requests
from abc import ABCMeta, abstractmethod

from models.order import Order
from models.watchlist import Watchlist

from data.data_client import DataClient
from common.helper import Notifier


class OrderStatus(Enum):
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELED = "CANCELLED"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class TradingClient(metaclass=ABCMeta):
    def __init__ (self, headers, data_client: DataClient, notifier: Notifier): 
        self.headers = headers
        self.data_client = data_client
        self.notifier = notifier
        
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
    def process_sell(self) -> bool:
        pass

    @abstractmethod
    def is_runnable(self) -> bool:
        return True

    @abstractmethod
    def get_latest_bar(self, symbol: str):
        pass

    @abstractmethod
    def process_buy(self) -> bool:
        pass
    
    @abstractmethod
    def process_rebuy(self, w: Watchlist):
        pass

    @abstractmethod
    def sell(self, w: Watchlist, o: Order):
        pass    

    @abstractmethod
    def buy(self, w: Watchlist):
        pass

    def create_order_obj(self) -> Order:
        pass
