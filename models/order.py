from datetime import datetime, UTC
from dataclasses import dataclass

from bson import ObjectId

from models.base import BaseModel, Type


@dataclass
class Order(BaseModel):
    _id: ObjectId = None
    type: Type = None
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
    sell_at_utc: datetime | None = None
    sell_session: str = None

    def calculate_profit(self):
        self.profit = round((self.sell_price - self.buy_price) * self.quantity, 2)