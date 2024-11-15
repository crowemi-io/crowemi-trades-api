import json
import os
from datetime import datetime, UTC
from dataclasses import dataclass, asdict, fields

from bson import ObjectId

IGNORE_FIELDS = ["_id"]


@dataclass
class BaseModel():
    created_at: datetime = datetime(1970, 1, 1, 0, 0, 0, 0, UTC)
    created_at_session: str = None
    updated_at: datetime = datetime(1970, 1, 1, 0, 0, 0, 0, UTC)
    updated_at_session: str = None

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        field_names = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)
    
    @classmethod
    def from_mongo(cls, mongo_dict):
        field_names = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in mongo_dict.items() if k in field_names}
        return cls(**filtered_data)

    def to_json(self):
        return json.dumps(asdict(self))
    
    def to_mongo(self) -> dict:
        ret = dict()
        for f in fields(self):
            # we don't want to return the mongodb _id field
            if f.name not in IGNORE_FIELDS:
                ret[f.name] = getattr(self, f.name)
        return ret

@dataclass
class Watchlist(BaseModel):
    _id: ObjectId = None
    symbol: str = None
    is_active: bool = True
    last_buy_at: datetime = None
    last_buy_session: str = None
    last_sell_at: datetime = None
    last_sell_session: str = None
    total_buy: int = 0
    total_sell: int = 0
    total_profit: float = 0.0

    def update_buy(self, session_id: str):
        self.last_buy_at = datetime.now(UTC)
        self.total_buy = (self.total_buy + 1)
        self.updated_at = datetime.now(UTC)
        self.updated_at_session = session_id
    
    def update_sell(self, session_id: str, profit: float = 0.0):
        self.last_sell_at = datetime.now(UTC)
        self.total_sell = (self.total_sell + 1)
        # TODO: add total profit calculation
        self.updated_at = datetime.now(UTC)
        self.updated_at_session = session_id
        self.total_profit = self.total_profit + profit

@dataclass
class OrderBatch(BaseModel):
    _id: ObjectId = None
    symbol: str = None
    quantity: float = None
    notional: float = None
    profit: float = None

    buy_order_id: str = None
    buy_status: str = None
    buy_price: float = 0
    buy_at_utc: datetime = datetime(1970, 1, 1, 0, 0, 0, 0, UTC)
    buy_session: str = None

    sell_order_id: str = None
    sell_status: str = None
    sell_price: float = 0
    sell_at_utc: datetime = datetime(1970, 1, 1, 0, 0, 0, 0, UTC)
    sell_session: str = None

    def calculate_profit(self):
        self.profit = round((self.sell_price - self.buy_price) * self.quantity, 2)
