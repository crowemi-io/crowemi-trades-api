import requests
from datetime import datetime, timedelta, UTC

from models.order import Order
from models.watchlist import Watchlist

from trading.trading_client import TradingClient

from common.helper import Helper

        
class AlpacaClient(TradingClient):
    def __init__(self, api_key, api_secret_key):
        self.headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret_key
        }
        super().__init__(self.headers)


class AlpacaTradingClient(AlpacaClient):
    def __init__(self, api_key: str, api_secret_key: str, base_url: str, data_base_url: str):
        super().__init__(api_key, api_secret_key)
        
        self.base_url = base_url
        self.data_base_url = data_base_url
        self.strict_pdt = True


    def is_runable(self) -> tuple[bool, dict]:
        # is the market open?
        clock = self.get_clock()
        if not clock['is_open']:
            # if the market is closed, exit the application (unless debug is enabled)
            return False, { "message": f"Market is closed. Skipping stocks.", "obj": { "clock": clock } }
        else:
            return True, None

    def process_sell(self, o: list[Order], w: Watchlist, lc: float, lb: dict) -> tuple[list[Order], list[dict]]:
        logs = list[dict]
        sell_orders = list[Order]
        # IMPORTANT! we should sell stock before we buy
        if self.strict_pdt:
            # we need to skip the sell if we purchased the stock today
            pdt = [order for order in o if order.buy_at_utc.date() == datetime.now(UTC).date()]
            if len(pdt) > 0:
                logs.append({
                    'message': f"Stock {w.symbol} was purchased today {datetime.now(UTC).date()}", 
                    'symbol': w.symbol, 
                })
                return sell_orders, logs

        end_date = datetime.now(UTC) # we want today minus thirty days for the calculation
        start_date = end_date - timedelta(days=45)
        # gets the historical bars for calculating the average daily swing
        bars = self.get_historical_bars(w.symbol, "1D", 1000, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        avg_daily_swing_25 = Helper.process_bar(bars, 30)["avg_daily_swing_25"]
        logs.append({
            'message': f"Stock {w.symbol} 25% average daily swing {avg_daily_swing_25}.", 
            'symbol': w.symbol
        })
        for order in o:
            # sell if the stock has increased by 25% of the average daily swing for previous 30 days
            target_price = round((order.buy_price + avg_daily_swing_25), 2)
            latest_price = float(lb[w.symbol]['c'])
            logs.append({
                'message': f"Target price: {target_price}; Latest bar: {latest_price}", 
                'symbol': w.symbol
            })
            if target_price <= latest_price:
                sell_orders.append(order)
        return sell_orders, logs

    def rebuy(self, order_batch: list[Order], a: Watchlist, lc: float) -> tuple[bool, list[dict]]:
        # Don’t buy within some percentage of all-time high, last six month (e.g. 10%) 🔥
        '''This is the logic for determining if we should rebuy a stock'''
        logs = list[dict]
        rebuy = False
        if len(order_batch) < a.total_allowed_batches:
            #   1. the previous buy has dropped by 2.5%
            last_order = max(order_batch, key=lambda obj: obj.created_at)
            rebuy_price = last_order.buy_price - (last_order.buy_price * .025)
            logs.append({
                'message': f"Rebuy price {rebuy_price}; Last close price {lc}", 
                'symbol': a.symbol
            })
            if lc <= rebuy_price:
                logs.append({
                    'message': f"Rebuying stock {a.symbol}; last order {last_order.buy_price}; last close {lc}", 
                    'symbol': a.symbol
                })
                return True, logs
            else:
                logs.append({
                    'message': f"Last close greater than rebuy, no rebuy {a.symbol}", 
                    'symbol': a.symbol
                })
                return False, logs
    
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
