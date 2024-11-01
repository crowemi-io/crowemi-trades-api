import os
import json
import uuid

from common.helper import Helper
from common.alpaca import TradingClient, TradingDataClient

from data.client import DataClient
from data.models import Watchlist


API_KEY = os.getenv("API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
API_URL_BASE = os.getenv("API_URL_BASE")
DATA_API_URL_BASE = os.getenv("DATA_API_URL_BASE")

TRADING_CLIENT = TradingClient(API_KEY, API_SECRET_KEY, API_URL_BASE)
DATA_CLIENT = TradingDataClient(API_KEY, API_SECRET_KEY, DATA_API_URL_BASE)
MONGO_CLIENT = DataClient(os.getenv("MONGODB_URI"))

SESSION_ID = uuid.uuid4().hex

DEFAULT_SYMBOLS = [
    "AAPL",
    "GOOG",
    "META",
    "TSLA",
    "AMZN",
    "MSFT",
    "NVDA"
]


# paper=True enables paper trading
def main():
    '''
    1. get symbols in play 
    2. get current position data
    3. determine if action is needed:
        - buy:
        - sell:
    '''
    # TODO: fix the logging :(
    MONGO_CLIENT.log("Starting trading bot", SESSION_ID, "info")

    ret = MONGO_CLIENT.read("watchlist", {"is_active": True})
    r = [Watchlist.from_mongo(doc) for doc in ret]

    print(ret)

    a = Watchlist("AAPL")    
    b = a.to_json()
    c = Watchlist.from_json(b)
    print(c)


    if ret.status_code == 200:
        ret = json.loads(ret.content)
        print(ret)
 
    payload = {
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
        "notional": "10",
        "symbol": "AAPL"
    }
    order = TRADING_CLIENT.create_order(payload)
    order = json.loads(order.content)   

    ret = MONGO_CLIENT.write("trades", order) 
    print(order)


def buy():
    pass

def sell():
    pass

def data_points():
    response = TRADING_CLIENT.get_asset("AAPL")
    resp = json.loads(response.content)

    resp = DATA_CLIENT.get_snapshot("AAPL")
    appl_snapshot = json.loads(resp.content)

    current_open = appl_snapshot.get("dailyBar")['o']
    current_close = appl_snapshot.get("dailyBar")['c']

    bars = DATA_CLIENT.get_historical_bars("AAPL", "1D", 1000, '2024-01-01', '2024-10-29')
    bars = json.loads(bars.content)
    # what is the average swing of the stock, last 30 days
    day_30 = bars.get("bars")[0:30]
    daily_swing = list(map(lambda x: x["h"] - x["l"], day_30))
    avg_daily_swing_30 = sum(daily_swing) / len(daily_swing)
    day_30_high = max(list(map(lambda x: x["h"], day_30)))
    day_30_low = min(list(map(lambda x: x["l"], day_30)))
    
    # percent change from 30 day high
    percent_change_30_high = Helper.percent_change(day_30_high, current_close)

    sell_point = (current_open * .0025) + current_open

def process_hourly_bar() -> bool:
    """`Process Hourly Bar`
    this method takes an hourly bar and processes it to determine if a buy or sell signal is present. 
    ---
    Returns:
        bool: True if a buy signal is present, False otherwise
    """
    pass



if __name__ == '__main__':
    main()

