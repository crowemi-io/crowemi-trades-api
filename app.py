import os
import json
import uuid
from datetime import datetime, timedelta, UTC

from common.helper import Helper
from common.alpaca import TradingClient, TradingDataClient

from data.client import DataClient, LogLevel
from data.models import Watchlist, OrderBatch


API_KEY = os.getenv("API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
API_URL_BASE = os.getenv("API_URL_BASE")
DATA_API_URL_BASE = os.getenv("DATA_API_URL_BASE")

TRADING_CLIENT = TradingClient(API_KEY, API_SECRET_KEY, API_URL_BASE)
DATA_CLIENT = TradingDataClient(API_KEY, API_SECRET_KEY, DATA_API_URL_BASE)
MONGO_CLIENT = DataClient(os.getenv("MONGODB_URI"))

DEBUG = os.getenv("DEBUG", False)
SESSION_ID = uuid.uuid4().hex
BATCH_SIZE = 10

DEFAULT_SYMBOLS = [
    "AAPL",
    "GOOG",
    "META",
    "TSLA",
    "AMZN",
    "MSFT",
    "NVDA"
]


def main():
    # 1. get symbols in play 
    MONGO_CLIENT.log("Start", SESSION_ID, LogLevel.INFO)
    # is the market open?
    clock = json.loads(TRADING_CLIENT.get_clock().content)
    if not clock['is_open']:
        # if the market is closed, exit the application (unless debug is enabled)
        MONGO_CLIENT.log(f"Market is closed.", SESSION_ID, LogLevel.WARNING, {"clock": clock})
        if not DEBUG:
            exit(0)
    
    active_symbols = [Watchlist.from_mongo(doc) for doc in MONGO_CLIENT.read("watchlist", {"is_active": True})]

    # 2. get current position data
    for a in active_symbols:
        order_batch = MONGO_CLIENT.read("orders", {"symbol": a.symbol})
        # no open orders
        if not order_batch:
            MONGO_CLIENT.log(f"No active orders {a.symbol}; running entry.", SESSION_ID, "info")
            # should we enter a position?
            if entry(a.symbol):
                MONGO_CLIENT.log(f"Entering position for {a.symbol}.", SESSION_ID, "info")
                buy(a, BATCH_SIZE)
            else:
                MONGO_CLIENT.log(f"No entry point found for {a.symbol}", SESSION_ID, "info")
        # open orders
        else:
            MONGO_CLIENT.log(f"Active orders found {a.symbol}; running sell.", SESSION_ID, "info")
            # determine if we should sell
            #   1. the previous buy has increased by 2.5%
            # determine if we should buy
            #   1. the previous buy has dropped by 2.5%
            #   2. we have less than or equal to 5 open positions
            # sell(a.symbol)
    
    # 3. determine if action is needed

    MONGO_CLIENT.log("End", SESSION_ID, "info")

def entry(symbol: str) -> bool:
    ret = False # innocent until proven guilty
    snapshot = json.loads(DATA_CLIENT.get_snapshot(symbol).content)

    last_open = snapshot.get("dailyBar")['o']
    last_close = snapshot.get("dailyBar")['c']

    today = datetime.now(UTC)
    sixty_days = (today - timedelta(days=60))

    bars = DATA_CLIENT.get_historical_bars(symbol, "1D", 1000, f'{sixty_days.year}-{sixty_days.month:02}-{sixty_days.day:02}', f'{today.year}-{today.month:02}-{today.day:02}')
    bars = json.loads(bars.content)
    # process the last 7 days
    data = list()
    days = [30]
    total_bars = (len(bars.get("bars", None))-1) # we need to minus one since we add one while doing some calculations
    [data.append(process_bar(bars, d)) if d <= total_bars else None for d in days]

    # keep it simple for now, if the last close is less than 2.5% of the 30 day high, we will buy 
    if (last_close * .025) + last_close < data[0]["day_high"]:
        ret = True
    else:
        ret = False
    
    return ret

def buy(wl: Watchlist, notional: float):
    MONGO_CLIENT.log(f"buying stock {wl.symbol}@{notional}", SESSION_ID, "info")
    payload = {
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
        "notional": notional,
        "symbol": wl.symbol
    }
    MONGO_CLIENT.log(f"buying stock {wl.symbol}@{notional}", SESSION_ID, LogLevel.INFO, payload)
    order = json.loads(TRADING_CLIENT.create_order(payload).content)   
    # what data points do we need to capture for our trade?
    # sell_point = (current_open * .0025) + current_open 2024-11-07T02:58:52.270622125Z
    order_batch = OrderBatch(
        symbol = order.get("symbol", None),
        quantity = order.get("qty", None),
        notional = notional,
        status = order.get("status", None),
        buy_order_id = order.get("id", None),
        buy_price = order.get("price", None),
        buy_at_utc = None,
        buy_session = None,
        sell_order_id = None,
        sell_price = None,
        sell_at_utc = None,
        sell_session = None,
        created_at_session = SESSION_ID,
        created_at = datetime.fromisoformat(order.get("created_at", None)),
        updated_at_session = SESSION_ID,
        updated_at =  datetime.fromisoformat(order.get("updated_at", None))
    )    

    ret = MONGO_CLIENT.write("order", order_batch.get_write_obj())
    MONGO_CLIENT.update("watchlist", {"symbol": wl.symbol}, {"last_buy_at": datetime.now(UTC), "total_buy": (wl.total_buy + 1), "updated_at": datetime.now(UTC), "updated_at_session": SESSION_ID }, upsert=False)
    return ret 

def sell():
    pass

def process_bar(bars: dict, period: int) -> dict:
    # what is the average swing of the stock, last 7 days
    ret = dict()
    
    ret["period"] = period
    zero_based_period = (period - 1)
    ret["zero_based_period"] = zero_based_period

    last = bars.get("bars")[0]
    ret["last"] = last
    current = bars.get("bars")[zero_based_period]
    ret["current"] = current
    previous = bars.get("bars")[zero_based_period + 1]
    ret["previous"] = previous

    day = bars.get("bars")[0:zero_based_period]
    daily_swing = list(map(lambda x: x["h"] - x["l"], day))
    avg_daily_swing = sum(daily_swing) / len(daily_swing)
    ret["avg_daily_swing"] = avg_daily_swing  

    day_high = max(list(map(lambda x: x["h"], day)))
    ret["day_high"] = day_high 
    day_low = min(list(map(lambda x: x["l"], day)))
    ret["day_low"] = day_low 

    percent_change = Helper.percent_change(day_high, last["c"])
    ret["percent_change"] = percent_change
    current_percent_change = Helper.percent_change(previous['c'], current['c'])
    ret["current_percent_change"] = current_percent_change

    return ret


if __name__ == '__main__':
    main()
