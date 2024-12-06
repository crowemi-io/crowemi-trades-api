import json
from datetime import datetime, UTC
from dataclasses import dataclass, asdict, fields

from bson import ObjectId, json_util

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
        return json_util.dumps(asdict(self))
    
    def to_mongo(self) -> dict:
        ret = dict()
        for f in fields(self):
            # we don't want to return the mongodb _id field
            if f.name not in IGNORE_FIELDS:
                ret[f.name] = getattr(self, f.name)
        return ret
