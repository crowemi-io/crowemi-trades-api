import requests
from datetime import datetime, timedelta, UTC

from models.base import AssetType
from models.order import Order
from models.watchlist import Watchlist
from data.data_client import DataClient, LogLevel
from trading.trading_client import TradingClient
from common.helper import Helper, Notifier


class AlpacaTradingClient(TradingClient):
    def __init__(self, api_key: str, api_secret_key: str, base_url: str, data_base_url: str, data_client: DataClient, notifier: Notifier = None):
        self.headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret_key
        }
        super().__init__(self.headers, data_client, notifier)
        
        self.base_url = base_url
        self.data_base_url = data_base_url
        self.strict_pdt = False


    def is_runnable(self) -> bool:
        # is the market open?
        clock = self.get_clock()
        if not clock['is_open']:
            # if the market is closed, exit the application (unless debug is enabled)
            message = f"Market is closed. Skipping stocks."
            self.data_client.log(
                message, 
                LogLevel.INFO,
                obj={ "message": message, "obj": { "clock": clock } }
            )
            return False
        else:
            return True

    def process_sell(self, o: list[Order], w: Watchlist, lc: float, lb: dict) -> None:
        # IMPORTANT! we should sell stock before we buy
        if self.strict_pdt:
            # we need to skip the sell if we purchased the stock today
            pdt = [order for order in o if order.buy_at_utc.date() == datetime.now(UTC).date()]
            if len(pdt) > 0:
                self.data_client.log(
                    message=f"Stock {w.symbol} was purchased today {datetime.now(UTC).date()}", 
                    symbol=w.symbol, 
                    log_level=LogLevel.INFO
                )
                return False

        end_date = datetime.now(UTC) # we want today minus thirty days for the calculation
        start_date = end_date - timedelta(days=45)
        # gets the historical bars for calculating the average daily swing
        bars = self.get_historical_bars(w.symbol, "1D", 1000, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        avg_daily_swing_25 = Helper.process_bar(bars, 30)["avg_daily_swing_25"]
        self.data_client.log(
            message=f"Stock {w.symbol} 25% average daily swing {avg_daily_swing_25}.",
            symbol=w.symbol,
            log_level=LogLevel.INFO
        )

        for order in o:
            # sell if the stock has increased by 25% of the average daily swing for previous 30 days
            target_price = round((order.buy_price + avg_daily_swing_25), 2)
            latest_price = float(lb[w.symbol]['c'])
            self.data_client.log(
                message=f"Target price: {target_price}; Latest bar: {latest_price}",
                symbol=w.symbol,
                log_level=LogLevel.INFO
            )
            if target_price <= latest_price:
                self.sell(w, order)

    def process_buy(self, order_batch: list[Order], a: Watchlist, lc: float) -> bool:
        '''This is the logic for determining if we should rebuy a stock'''
        if len(order_batch) < a.total_allowed_batches:
            #   1. the previous buy has dropped by 2.5%
            last_order = max(order_batch, key=lambda obj: obj.created_at)
            rebuy_price = last_order.buy_price - (last_order.buy_price * .025)
            self.data_client.log(
                message=f"Rebuy price {rebuy_price}; Last close price {lc}", 
                symbol=a.symbol
            )

            if lc <= rebuy_price:
                self.data_client.log(
                    message=f"Rebuying stock {a.symbol}; last order {last_order.buy_price}; last close {lc}", 
                    symbol=a.symbol
                )
                self.buy(a)
                return True
            else:
                self.data_client.log(
                    message=f"Last close greater than rebuy, no rebuy {a.symbol}", 
                    symbol=a.symbol
                )
                return False

    def buy(self, w: Watchlist) -> bool:
        status: bool = False
        try:
            # notional/batch_size is a dollar amount
            payload = {
                "side": "buy",
                "type": "market",
                "time_in_force": "day",
                "notional": w.batch_size,
                "symbol": w.symbol
            }
            log_message = f"buying stock {w.symbol}@{w.batch_size}"
            self.data_client.log(
                message=f"buying stock {w.symbol}@{w.batch_size}", 
                symbol=w.symbol, 
                log_level=LogLevel.INFO, 
                obj=payload
            )

            order = self.create_order(payload)
            if not order.get("status", None) == "filled":
                # sometimes the order doesn't process immediately
                order = self.get_order(w.symbol, order.get("id"))

            if order:
                # creates a new order object
                new_order: Order = self.create_order_obj(order)
                self.data_client.write("order", new_order.to_mongo())

                w.update_buy(self.data_client.session_id)
                self.data_client.update("watchlist", {"symbol": w.symbol}, w.to_mongo(), upsert=False)
                self.notifier.alert(log_message)

                status = True
            else:
                self.data_client.log(
                    message=f"Error buying stock {w.symbol}", 
                    symbol=w.symbol, 
                    log_level=LogLevel.ERROR, 
                    obj={"error": "order not found in API with ID created"}
                )

        except Exception as e:
            self.data_client.log(
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
            self.data_client.log(
                message=f"selling stock {w.symbol}", 
                symbol=w.symbol, 
                log_level=LogLevel.INFO, 
                obj=payload
            )
            # create sell order on alpaca
            order = self.create_order(payload)
            self.data_client.log(
                message=f"Success selling stock {w.symbol}", 
                symbol=w.symbol, 
                log_level=LogLevel.INFO, 
                obj=order
            )

            if not order.get("status", None) == "filled":
                # sometimes the order doesn't process immediately
                filled_order = self.get_order(order_id=order.get("id"))
                if filled_order:
                    order = filled_order

            o.sell_order_id = order.get("id", None)
            o.sell_status = order.get("status", None)
            filled_avg_price = order.get("filled_avg_price", 0)
            if filled_avg_price:
                o.sell_price = float(filled_avg_price)
            o.sell_at_utc = datetime.now(UTC)
            o.sell_session = self.data_client.session_id

            o.calculate_profit()
            
            self.data_client.update("order", {"_id": o._id}, o.to_mongo(), upsert=False)

            w.update_sell(self.data_client.session_id, o.profit)
            self.notifier.alert(f"selling stock {w.symbol}; Profit {o.profit}")
        except Exception as e:
            self.data_client.log(
                message=f"Error selling stock {w.symbol}", 
                symbol=w.symbol, 
                log_level=LogLevel.ERROR, 
                obj={"error": str(e)}
            )

    def create_order_obj(self, order) -> Order:
        filled_avg_price = order.get("filled_avg_price", None)
        filled_avg_price = float(filled_avg_price) if filled_avg_price else None
        filled_qty = order.get("filled_qty", None)
        filled_qty = float(filled_qty) if filled_qty else None
        notional = order.get("notional", None)
        notional = float(order.get("notional", None)) if filled_qty else None
        
        if order.get("filled_at", None):
            filled_at = datetime.fromisoformat(order.get("filled_at", None))
        else:
            filled_at = None

        # process order dates
        if order.get("created_at", None):
            created_at = datetime.fromisoformat(order.get("created_at", None))
        else:
            created_at = None
        if order.get("updated_at", None):
            updated_at = datetime.fromisoformat(order.get("updated_at", None))
        else:
            updated_at = None

        try:
            order = Order(
                symbol = order.get("symbol", None),
                type = AssetType.STOCK.value,
                quantity = filled_qty,
                notional = notional,
                buy_status = order.get("status", None),
                buy_order_id = order.get("id", None),
                buy_price = filled_avg_price,
                buy_at_utc = filled_at,
                buy_session = self.data_client.session_id,
                created_at_session = self.data_client.session_id,
                created_at = created_at,
                updated_at_session = self.data_client.session_id,
                updated_at = updated_at
            )
        except Exception as e:
            print(f"Error creating order: {e}")
            self.data_client.log(
                message=f"Error creating order: {e}", 
                log_level=LogLevel.ERROR, 
                obj=order)
            return None
        
        return order

    # api methods
    def get_account(self):
        return requests.get(f"{self.base_url}/v2/account", headers=self.headers)

    def get_asset(self, asset: str):
        return self.get(f"{self.base_url}/v2/assets/{asset}")

    def get_order(self, symbol: str = None, order_id: str = None, status: str = 'all') -> list:
        if order_id:
            return self.get(f"{self.base_url}/v2/orders/{order_id}")
        else:
            endpoint = f"{self.base_url}/v2/orders?status={status}"
            if symbol:
                endpoint += f"&symbols={symbol}"

            return self.get(endpoint)
        
    def get_watchlist(self):
        return self.get(f"{self.base_url}/v2/watchlists")
        
    def get_clock(self):
        return self.get(f"{self.base_url}/v2/clock")
    
    def get_positions(self):
        return self.get(f"{self.base_url}/v2/positions")

    def create_order(self, payload: str):
        return self.post(f"{self.base_url}/v2/orders", payload)
    
    def create_watchlist(self, name: str, symbols: list[str]):
        return self.post(f"{self.base_url}/v2/watchlist", {"name": name, "symbols": symbols})

    # data
    def get_latest_bar(self, symbol: str, feed: str = "iex"):
        return self.get(f"{self.data_base_url}/v2/stocks/bars/latest?symbols={symbol}&feed={feed}")['bars']

    def get_latest_quote(self, symbol: str, feed: str = "iex"):
        return self.get(f"{self.data_base_url}/v2/stocks/quotes/latest?symbols={symbol}&feed={feed}")

    def get_snapshot(self, asset: str, feed: str = "iex"):
        url = f"{self.data_base_url}/v2/stocks/{asset}/snapshot?feed={feed}"
        return self.get(url)
    
    def get_historical_bars(self, asset: str, timeframe: str, limit: int, start: str, end: str):
        '''Gets the historical bars for a given asset, within the specified timeframe for regular trading days.'''
        url = f"{self.data_base_url}/v2/stocks/{asset}/bars?timeframe={timeframe}&start={start}&end={end}&limit={limit}&adjustment=raw&feed=iex&sort=desc"
        r = self.get(url)
        return r

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
        # if symbol:
        #     orders = self.alpaca_trading_client.get_order(symbol=symbol)
        # else:
        #     orders = self.alpaca_trading_client.get_order()
        # for order in orders:
        #     side = order.get("side")
        #     if side == "buy":
        #         matching_order = self.mongo_client.read("order", {"buy_order_id": order.get("id")})
        #         if not matching_order:
        #             ret = True
        #             print(f"buy: {order.get("id")} {order.get("symbol")} created at {order.get("created_at")}")
        #     if side == "sell":
        #         matching_order = self.mongo_client.read("order", {"sell_order_id": order.get("id")})
        #         if not matching_order:
        #             ret = True
        #             print(f"sell: {order.get("id")} {order.get("symbol")} created at {order.get("created_at")}")
        return ret
