import json
import os
import uuid
from datetime import datetime, timedelta, UTC

from common.helper import Helper
from common.alpaca import TradingClient, TradingDataClient, alert_channel

from data.client import DataClient, LogLevel
from data.models import Watchlist, Order

CONFIG = Helper.convert_config(os.getenv("CONFIG", None))

class Trader():

    TOTAL_ALLOWED_BATCHES = 5
    BATCH_SIZE = 20
    STRICT_PDT = True
    OVERRIDE_ENTRY = True
    SESSION_ID = uuid.uuid4().hex

    def __init__(self, config: dict = CONFIG):
        self.api_key = config.get("api_key", None)
        self.api_secret_key = config.get("api_secret_key", None)
        self.api_url_base = config.get("api_url_base", None)
        self.data_api_url_base = config.get("data_api_url_base", None)
        self.bot_id = config.get("bot_id", None)
        self.bot_channel = config.get("bot_channel", None)
        self.trading_client = TradingClient(self.api_key, self.api_secret_key, self.api_url_base)
        self.data_client = TradingDataClient(self.api_key, self.api_secret_key, self.data_api_url_base)
        self.mongo_client = DataClient(config.get("uri", None))

        self.debug = config.get("debug", False)

    def run(self) -> bool:
        self.log("Start", LogLevel.INFO)
        if self.debug:
            self.log("Debug mode enabled", LogLevel.DEBUG)
            self.log(self.api_key, LogLevel.DEBUG)
            self.log(self.api_secret_key, LogLevel.DEBUG)
            self.log(self.api_url_base, LogLevel.DEBUG)
            self.log(self.data_api_url_base, LogLevel.DEBUG)

        # is the market open?
        clock = self.trading_client.get_clock()
        if not clock['is_open']:
            # if the market is closed, exit the application (unless debug is enabled)
            self.log(f"Market is closed.", LogLevel.WARNING, {"clock": clock})
            if not self.debug:
                return True
        
        active_symbols = [Watchlist.from_mongo(doc) for doc in self.mongo_client.read("watchlist", {"is_active": True})]

        for a in active_symbols:
            latest_bar = self.data_client.get_latest_bar(a.symbol)['bars']
            latest_close = float(latest_bar[a.symbol]['c'])
            # get all order from alpaca and all order the the database
            alpaca_orders = self.trading_client.get_orders(a.symbol)
            all_orders = [Order.from_mongo(doc) for doc in self.mongo_client.read("order", {"symbol": a.symbol})]
            missing_orders = [order for order in alpaca_orders if order.get("id") not in [o.buy_order_id for o in all_orders]]
            if missing_orders:
                self.log(f"Missing orders found {a.symbol}; total orders {len(missing_orders)}", LogLevel.WARNING)
                [self.mongo_client.write("order", order.to_mongo()) for order in missing_orders]

            # after updating orders, get those orders that have been filled
            open_orders = [Order.from_mongo(doc) for doc in self.mongo_client.read("order", {"symbol": a.symbol, "buy_status": "filled", "sell_status": None})]

            # no open orders
            if not open_orders:
                self.log(f"No active orders {a.symbol}; running entry.", LogLevel.INFO)
                if self.OVERRIDE_ENTRY:
                    if not self.debug:
                        self.buy(a, self.BATCH_SIZE) # TODO: pull batch size from watchlist
                else:
                    self.log(f"No entry point found for {a.symbol}", LogLevel.INFO)
            else:
                self.log(f"Active orders found {a.symbol}; total orders {len(open_orders)}; running sell.", LogLevel.INFO)
                # process sell criteria and execute sell if met
                self.process_sell(open_orders, a, latest_close, latest_bar)
                
                self.rebuy(open_orders, a, latest_close)

        self.log("End", LogLevel.INFO)
        return True
    
    def process_sell(self, o: Order, a: Watchlist, lc: float, lb: dict) -> bool:
        # IMPORTANT! we should sell stock before we buy
        if self.STRICT_PDT:
            # we need to skip the sell if we purchased the stock today
            pdt = [order for order in o if order.buy_at_utc.date() == datetime.now(UTC).date()]
            if len(pdt) > 0:
                self.log(f"Stock {a.symbol} was purchased today {datetime.now(UTC).date()}, skipping sell.", LogLevel.INFO)
                self.rebuy(o, a, lc)
                return False
        
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=60)
        bars = self.data_client.get_historical_bars(a.symbol, "1D", 1000, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        avg_daily_swing_25 = Helper.process_bar(bars, 30)["avg_daily_swing_25"]
        self.log(f"Stock {a.symbol} 25% average daily swing {avg_daily_swing_25}.", LogLevel.INFO)
        for order in o:
            # sell if the stock has increased by 25% of the average daily swing for previous 30 days
            target_price = round((order.buy_price + avg_daily_swing_25), 2)
            latest_price = float(lb[a.symbol]['c'])
            self.log(f"Target price: {target_price}; Latest bar: {latest_price}", LogLevel.INFO)
            if target_price <= latest_price:
                self.sell(a, order)
        return True

    def rebuy(self, order_batch: Order, a: Watchlist, lc: float):
        if len(order_batch) <= self.TOTAL_ALLOWED_BATCHES:
            #   1. the previous buy has dropped by 2.5%
            last_order = max(order_batch, key=lambda obj: obj.created_at)
            rebuy_price = last_order.buy_price - (last_order.buy_price * .025)
            self.log(f"Rebuy price {rebuy_price}; Last order price {last_order.buy_price}", LogLevel.INFO)
            if lc <= rebuy_price:
                self.log(f"Rebuying stock {a.symbol}; last order {last_order.buy_price}; current price {lc}", LogLevel.INFO)
                if not self.debug:
                    self.buy(a, self.BATCH_SIZE)
            else:
                self.log(f"No entry point found for {a.symbol}", LogLevel.INFO)

    def log(self, message: str, log_level: str = "info", obj: dict = None):
        print(f"crowemi-trades: {self.SESSION_ID} {log_level}: {message}")
        if obj:
            print(f"crowemi-trades: {self.SESSION_ID} {log_level}: {obj}")
        self.mongo_client.log(message, self.SESSION_ID, log_level, obj)

    def buy(self, w: Watchlist, notional: float):
        try:
            payload = {
                "side": "buy",
                "type": "market",
                "time_in_force": "day",
                "notional": notional,
                "symbol": w.symbol
            }
            log_message = f"buying stock {w.symbol}@{notional}"
            self.log(f"buying stock {w.symbol}@{notional}", LogLevel.INFO, payload)
            order = self.trading_client.create_order(payload)
            if order.get("status", None) == "pending_new":
                # sometimes the order doesn't process immediately
                order = self.trading_client.get_order(order.get("id"))

            order_batch = create_order_batch(order)
            self.mongo_client.write("order", order_batch.to_mongo())

            w.update_buy(self.SESSION_ID)
            self.mongo_client.update("watchlist", {"symbol": w.symbol}, w.to_mongo(), upsert=False)
            alert_channel(log_message, self.bot_id, self.bot_channel)

        except Exception as e:
            self.log(f"Error buying stock {w.symbol}", LogLevel.ERROR, {"error": str(e)})

    def sell(self, w: Watchlist, o: Order):
        try:
            payload = {
                "side": "sell",
                "type": "market",
                "time_in_force": "day",
                "qty": o.quantity,
                "symbol": w.symbol
            }
            self.mongo_client.log(f"selling stock {w.symbol}", LogLevel.INFO, payload)
            order = self.trading_client.create_order(payload)
            if order.get("status", None) == "pending_new":
                # sometimes the order doesn't process immediately
                order = self.trading_client.get_order(order.get("id"))

            o.sell_order_id = order.get("id", None)
            o.sell_status = order.get("status", None)
            o.sell_price = float(order.get("filled_avg_price", None))
            o.sell_at_utc = datetime.now(UTC)
            o.sell_session = self.SESSION_ID

            o.calculate_profit()
            
            self.mongo_client.update("order", {"_id": o._id}, o.to_mongo(), upsert=False)

            w.update_sell(self.SESSION_ID, o.profit)
            alert_channel(f"selling stock {w.symbol}; Profit {o.profit}", self.bot_id, self.bot_channel)
        except Exception as e:
            self.log(f"Error selling stock {w.symbol}", LogLevel.ERROR, {"error": str(e)})


def create_order_batch(order, session_id) -> Order:
    filled_avg_price = order.get("filled_avg_price", None)
    filled_avg_price = float(filled_avg_price) if filled_avg_price else None
    filled_qty = order.get("filled_qty", None)
    filled_qty = float(filled_qty) if filled_qty else None

    order_batch = Order(
        symbol = order.get("symbol", None),
        quantity = filled_qty,
        notional = order.get("notional", None),
        buy_status = order.get("status", None),
        buy_order_id = order.get("id", None),
        buy_price = filled_avg_price,
        buy_at_utc = datetime.now(UTC),
        buy_session = session_id,
        created_at_session = session_id,
        created_at = datetime.fromisoformat(order.get("created_at", None)),
        updated_at_session = session_id,
        updated_at = datetime.fromisoformat(order.get("updated_at", None))
    )
    
    return order_batch




if __name__ == '__main__':
    Trader(CONFIG).run()
