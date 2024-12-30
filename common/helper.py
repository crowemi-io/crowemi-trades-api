import base64
import json
import requests
from datetime import datetime, timedelta, UTC

from abc import ABC, abstractmethod


def get_local_config() -> dict:
    with open(".secret/config-local.json", "r") as f:
        config = json.loads(f.read())
    return config



class Notifier(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def alert():
        pass

class TelegramNotifier(Notifier):
    def __init__(self, bot_id: str, channel_id: str = "-1002416451737"):
        self.bot_id = bot_id
        self.channel_id = channel_id

    def alert(self, message: str, bot_id: str = None, channel_id: str = None):
        # checks overrides
        if not bot_id:
            bot_id = self.bot_id
        if not channel_id:
            channel_id = self.channel_id

        uri = f"https://api.telegram.org/bot{bot_id}/sendMessage?chat_id={channel_id}&text={message}"
        ret = requests.get(uri)
        return ret


class Helper():
    @staticmethod
    def percent_change(old_value, new_value):
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def convert_config(b64: str | None) -> dict | None:
        if b64:
            try:
                config = base64.b64decode(b64).decode("utf-8")
                return json.loads(config)
            except Exception as e:
                print(f"Error reading config file: {e}")
                return None
    
    @staticmethod
    def process_bar(bars: dict, period: int) -> dict:
        # what is the average swing of the stock, last 7 days
        ret = dict()
        
        last = bars.get("bars")[0]
        ret["last"] = last

        day = bars.get("bars")[0:period]
        daily_swing = list(map(lambda x: x["h"] - x["l"], day))
        avg_daily_swing = sum(daily_swing) / len(daily_swing)
        ret["avg_daily_swing"] = avg_daily_swing  
        ret["avg_daily_swing_25"] = avg_daily_swing * 0.25
        ret["avg_daily_swing_50"] = avg_daily_swing * 0.50
        ret["avg_daily_swing_75"] = avg_daily_swing * 0.75

        day_high = max(list(map(lambda x: x["h"], day)))
        ret["day_high"] = day_high 
        day_low = min(list(map(lambda x: x["l"], day)))
        ret["day_low"] = day_low 

        percent_change = Helper.percent_change(day_high, last["c"])
        ret["percent_change"] = percent_change

        return ret

    @staticmethod
    def calculate_profit(records: dict) -> dict:
        ret = dict()
        
        today = 0.0
        last_30 = 0.0
        last_60 = 0.0
        all_time = 0.0
        symbols = dict()

        for record in records:
            if record.sell_at_utc.date() == datetime.now(UTC).date():
                today += record.profit
            if record.sell_at_utc.date() <= datetime.now(UTC).date() + timedelta(days=30):
                last_30 += record.profit
            if record.sell_at_utc.date() <= datetime.now(UTC).date() + timedelta(days=60):
                last_60 += record.profit
            
            all_time += record.profit
            
            if record.symbol not in ret:
                symbols[f'{record.symbol}'] = 0
            symbols[f'{record.symbol}'] += record.profit
        
        ret["today"] = today
        ret["last_30"] = last_30
        ret["last_60"] = last_60
        ret["all_time"] = all_time
        ret["symbols"] = symbols

        return ret