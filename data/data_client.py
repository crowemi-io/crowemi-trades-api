from datetime import datetime, UTC
from pymongo import MongoClient
import uuid

class LogLevel:
    INFO = "info"
    ERROR = "error"
    WARNING = "warning"
    DEBUG = "debug"

# TODO: convert this to mongo client
class DataClient():
    def __init__(self, uri: str, database: str = "crowemi-trades", session_id: str = None):
        if not session_id:
            session_id = uuid.uuid4().hex
        
        self.session_id = session_id
        self.client: MongoClient = MongoClient(uri)
        self.db = self.client.get_database(database)

    def log(self, message: str, log_level: str = LogLevel.INFO, symbol: str = None, obj: dict = None):
        print(f"crowemi-trades: {self.session_id} {log_level}: {message}")
        if obj:
            print(f"crowemi-trades: {self.session_id} {log_level}: {obj}")
        self.write("log", {"created_at": datetime.now(UTC), "message": message, "level": log_level, "symbol": symbol, "obj": obj, "session": self.session_id})

    def read(self, collection: str, query: dict):
        try:
            ret = list()
            res = self.db.get_collection(collection).find(query)
            [ret.append(doc) for doc in res]
            return ret
        except Exception as e:
            raise e

    def write(self, collection: str, data: dict):
        try:
            ret = self.db.get_collection(collection).insert_one(data)
            return ret
        except Exception as e:
            raise e

    def update(self, collection: str, query: dict, data: dict, upsert: bool = False):
        return self.db.get_collection(collection).update_one(query, {"$set": data}, upsert=upsert)
