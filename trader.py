import json
import os
import uuid
from datetime import datetime, timedelta, UTC

from common.helper import Helper
from trading.alpaca_client import TradingClient, TradingDataClient, alert_channel

from data.data_client import DataClient, LogLevel
from models.base import Watchlist, Order

CONFIG = Helper.convert_config(os.getenv("CONFIG", None))

class Trader():

    TOTAL_ALLOWED_BATCHES = 5
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
        self.extended_hours = False

        self.debug = config.get("debug", False)

    def _log(self, message: str, log_level: str = "info", symbol: str = None, obj: dict = None):
        print(f"crowemi-trades: {self.SESSION_ID} {log_level}: {message}")
        if obj:
            print(f"crowemi-trades: {self.SESSION_ID} {log_level}: {obj}")
        self.mongo_client.log(message, self.SESSION_ID, log_level, symbol, obj)
        if log_level == LogLevel.ERROR:
            alert_channel(f"crowemi-trades: {self.SESSION_ID} {log_level}: {message}", self.bot_id, self.bot_channel)

    def run(self) -> bool:
        self._log(message="Start", log_level=LogLevel.INFO)
        if self.debug:
            self._log(message="Debug mode enabled", log_level=LogLevel.DEBUG)
            self._log(message=self.api_key, log_level=LogLevel.DEBUG)
            self._log(message=self.api_secret_key, log_level=LogLevel.DEBUG)
            self._log(message=self.api_url_base, log_level=LogLevel.DEBUG)
            self._log(message=self.data_api_url_base, log_level=LogLevel.DEBUG)

        # is the market open?
        clock = self.trading_client.get_clock()
        if not clock['is_open']:
            # if the market is closed, exit the application (unless debug is enabled)
            self._log(
                message=f"Market is closed.", 
                log_level=LogLevel.WARNING, 
                obj={"clock": clock}
            )
            self.extended_hours = True
            if not self.debug:
                return True
        
        active_watchlists = [Watchlist.from_mongo(doc) for doc in self.mongo_client.read("watchlist", {"is_active": True})]

        for watchlist in active_watchlists:
            latest_bar = self.data_client.get_latest_bar(watchlist.symbol)['bars']
            last_close = float(latest_bar[watchlist.symbol]['c'])
            
            # get those orders that have not been filled
            open_orders = self.get_open_orders(watchlist.symbol)

            # no open orders
            if not open_orders:
                self._log(
                    message=f"No active orders {watchlist.symbol}; running entry.", 
                    log_level=LogLevel.INFO, 
                    symbol=watchlist.symbol
                )
                self.buy(watchlist, watchlist.batch_size) # TODO: pull batch size from watchlist
            else:
                self._log(
                    message=f"Active orders found {watchlist.symbol}; total orders {len(open_orders)}; running sell.", 
                    symbol=watchlist.symbol, 
                    log_level=LogLevel.INFO
                )
                # process sell criteria and execute sell if met
                self.process_sell(open_orders, watchlist, last_close, latest_bar)
                self.rebuy(open_orders, watchlist, last_close)

        self._log(
            message="End", 
            log_level=LogLevel.INFO
        )
        return True
    
    def process_sell(self, o: list[Order], w: Watchlist, lc: float, lb: dict) -> bool:
        # IMPORTANT! we should sell stock before we buy
        if self.STRICT_PDT:
            # we need to skip the sell if we purchased the stock today
            pdt = [order for order in o if order.buy_at_utc.date() == datetime.now(UTC).date()]
            if len(pdt) > 0:
                self._log(
                    message=f"Stock {w.symbol} was purchased today {datetime.now(UTC).date()}", 
                    symbol=w.symbol, 
                    log_level=LogLevel.INFO
                )
                return False
        
        end_date = datetime.now(UTC) # we want today minus thirty days for the calculation
        start_date = end_date - timedelta(days=45)
        # gets the historical bars for calculating the average daily swing
        bars = self.data_client.get_historical_bars(w.symbol, "1D", 1000, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        avg_daily_swing_25 = Helper.process_bar(bars, 30)["avg_daily_swing_25"]
        self._log(
            message=f"Stock {w.symbol} 25% average daily swing {avg_daily_swing_25}.", 
            symbol=w.symbol, 
            log_level=LogLevel.INFO
        )
        for order in o:
            # sell if the stock has increased by 25% of the average daily swing for previous 30 days
            target_price = round((order.buy_price + avg_daily_swing_25), 2)
            latest_price = float(lb[w.symbol]['c'])
            self._log(
                message=f"Target price: {target_price}; Latest bar: {latest_price}", 
                symbol=w.symbol, 
                log_level=LogLevel.INFO
            )
            if target_price <= latest_price:
                self.sell(w, order)
        return True

    def rebuy(self, order_batch: Order, a: Watchlist, lc: float):
        '''This is the logic for determining if we should rebuy a stock'''
        if len(order_batch) < a.total_allowed_batches:
            #   1. the previous buy has dropped by 2.5%
            last_order = max(order_batch, key=lambda obj: obj.created_at)
            rebuy_price = last_order.buy_price - (last_order.buy_price * .025)
            self._log(
                message=f"Rebuy price {rebuy_price}; Last close price {lc}", 
                symbol=a.symbol, 
                log_level=LogLevel.INFO
            )
            if lc <= rebuy_price:
                self._log(
                    message=f"Rebuying stock {a.symbol}; last order {last_order.buy_price}; last close {lc}", 
                    symbol=a.symbol, 
                    log_level=LogLevel.INFO
                )
                self.buy(a, a.batch_size)
            else:
                self._log(
                    message=f"Last close greater than rebuy, no rebuy {a.symbol}", 
                    symbol=a.symbol, 
                    log_level=LogLevel.INFO
                )

    def buy(self, w: Watchlist, notional: float) -> bool:
        status: bool = False
        if self.debug:
            self._log(
                message=f"Skipping buy {w.symbol}@{notional}", 
                symbol=w.symbol, 
                log_level=LogLevel.DEBUG
            )
            return status

        try:
            payload = {
                "side": "buy",
                "type": "market",
                "time_in_force": "day",
                "notional": notional,
                "symbol": w.symbol,
            }
            log_message = f"buying stock {w.symbol}@{notional}"
            self._log(
                message=f"buying stock {w.symbol}@{notional}", 
                symbol=w.symbol, 
                log_level=LogLevel.INFO, 
                obj=payload
            )

            order = self.trading_client.create_order(payload)
            if not order.get("status", None) == "filled":
                # sometimes the order doesn't process immediately
                order = self.trading_client.get_order(w.symbol, order.get("id"))

            if order:
                new_order: Order = self.create_order(order)
                self.mongo_client.write("order", new_order.to_mongo())

                w.update_buy(self.SESSION_ID)
                self.mongo_client.update("watchlist", {"symbol": w.symbol}, w.to_mongo(), upsert=False)
                # TODO: move this outside of function
                alert_channel(log_message, self.bot_id, self.bot_channel)

                status = True
            else:
                self._log(
                    message=f"Error buying stock {w.symbol}", 
                    symbol=w.symbol, 
                    log_level=LogLevel.ERROR, 
                    obj={"error": "order not found in API with ID created"}
                )

        except Exception as e:
            self._log(
                message=f"Error buying stock {w.symbol}", 
                symbol=w.symbol, 
                log_level=LogLevel.ERROR, 
                obj={"error": str(e)}
            )
        finally:
            return status

    def sell(self, w: Watchlist, o: Order):
        try:
            payload = {
                "side": "sell",
                "type": "market",
                "time_in_force": "day",
                "qty": o.quantity,
                "symbol": w.symbol
            }
            self._log(
                message=f"selling stock {w.symbol}", 
                symbol=w.symbol, 
                log_level=LogLevel.INFO, 
                obj=payload
            )
            # create sell order on alpaca
            order = self.trading_client.create_order(payload)
            self._log(
                message=f"Success selling stock {w.symbol}", 
                symbol=w.symbol, 
                log_level=LogLevel.INFO, 
                obj=order
            )

            if not order.get("status", None) == "filled":
                # sometimes the order doesn't process immediately
                filled_order = self.trading_client.get_order(order_id=order.get("id"))
                if filled_order:
                    order = filled_order

            o.sell_order_id = order.get("id", None)
            o.sell_status = order.get("status", None)
            filled_avg_price = order.get("filled_avg_price", 0)
            if filled_avg_price:
                o.sell_price = float(filled_avg_price)
            o.sell_at_utc = datetime.now(UTC)
            o.sell_session = self.SESSION_ID

            o.calculate_profit()
            
            self.mongo_client.update("order", {"_id": o._id}, o.to_mongo(), upsert=False)

            w.update_sell(self.SESSION_ID, o.profit)
            alert_channel(f"selling stock {w.symbol}; Profit {o.profit}", self.bot_id, self.bot_channel)
        except Exception as e:
            self._log(
                message=f"Error selling stock {w.symbol}", 
                symbol=w.symbol, 
                log_level=LogLevel.ERROR, 
                obj={"error": str(e)}
            )

    def backfill(self, symbol: str = None, dry_run: bool = True) -> bool:

        # this logic was originally in the run method, but was moved here not sure if its needed of if this is duplicated here :/
        # # get all order from alpaca and all order the the database
        # alpaca_orders = self.trading_client.get_order(a.symbol)
        # all_orders = [Order.from_mongo(doc) for doc in self.mongo_client.read("order", {"symbol": a.symbol})]
        # missing_orders = [order for order in alpaca_orders if order.get("id") not in [o.buy_order_id for o in all_orders]]
        # if missing_orders:
        #     self.log(f"Missing orders found {a.symbol}; total orders {len(missing_orders)}", LogLevel.WARNING)
        #     [self.mongo_client.write("order", order.to_mongo()) for order in missing_orders]

        ret = False
        if symbol:
            orders = self.trading_client.get_order(symbol=symbol)
        else:
            orders = self.trading_client.get_order()
        for order in orders:
            side = order.get("side")
            if side == "buy":
                matching_order = self.mongo_client.read("order", {"buy_order_id": order.get("id")})
                if not matching_order:
                    ret = True
                    print(f"buy: {order.get("id")} {order.get("symbol")} created at {order.get("created_at")}")
            if side == "sell":
                matching_order = self.mongo_client.read("order", {"sell_order_id": order.get("id")})
                if not matching_order:
                    ret = True
                    print(f"sell: {order.get("id")} {order.get("symbol")} created at {order.get("created_at")}")
        return ret

    def create_order(self, order) -> Order:
        filled_avg_price = order.get("filled_avg_price", None)
        filled_avg_price = float(filled_avg_price) if filled_avg_price else None
        filled_qty = order.get("filled_qty", None)
        filled_qty = float(filled_qty) if filled_qty else None
        filled_at = datetime.fromisoformat(order.get("filled_at", None))
        created_at = datetime.fromisoformat(order.get("created_at", None))
        updated_at = datetime.fromisoformat(order.get("updated_at", None))

        try:
            order = Order(
                symbol = order.get("symbol", None),
                quantity = filled_qty,
                notional = order.get("notional", None),
                buy_status = order.get("status", None),
                buy_order_id = order.get("id", None),
                buy_price = filled_avg_price,
                buy_at_utc = filled_at,
                buy_session = self.SESSION_ID,
                created_at_session = self.SESSION_ID,
                created_at = created_at,
                updated_at_session = self.SESSION_ID,
                updated_at = updated_at
            )
        except Exception as e:
            print(f"Error creating order: {e}")
            self._log(
                message=f"Error creating order: {e}", 
                log_level=LogLevel.ERROR, 
                obj=order)
            return None
        
        return order

    def get_open_orders(self, symbol: str) -> list[Order]:
        return [Order.from_mongo(doc) for doc in self.mongo_client.read("order", {"symbol": symbol, "buy_status": "filled", "sell_status": None})]



if __name__ == '__main__':
    Trader(CONFIG).run()
