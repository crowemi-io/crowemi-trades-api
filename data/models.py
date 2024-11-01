import json
from datetime import datetime, UTC
from dataclasses import dataclass, asdict, fields


@dataclass
class BaseModel():
    created_at: datetime = datetime.now(UTC)
    created_at_session: str = None
    updated_at: datetime = None
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
    
    def to_mongo(self):
        data = asdict(self)
        return data

@dataclass
class Watchlist(BaseModel):
    _id: str = None
    symbol: str = None
    is_active: bool = True
    last_buy_at: datetime = None
    last_sell_at: datetime = None
