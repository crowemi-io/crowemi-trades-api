from datetime import datetime, UTC
from dataclasses import dataclass

from bson import ObjectId

from models.base import BaseModel, Type

@dataclass
class Watchlist(BaseModel):
    _id: ObjectId = None
    type: Type = None
    symbol: str = None
    is_active: bool = True
    last_buy_at: datetime = None
    last_buy_session: str = None
    last_sell_at: datetime = None
    last_sell_session: str = None
    total_buy: int = 0
    total_sell: int = 0
    total_profit: float = 0.0
    extended_hours: bool = False
    batch_size: int = 20
    total_allowed_batches: int = 5


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
