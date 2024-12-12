import json
import os
import uuid
from datetime import datetime, timedelta, UTC

from common.helper import Helper, alert_channel
from trading.trading_client import TradingClient
from trading.alpaca_client import AlpacaTradingClient
from trading.coinbase_client import CoinbaseTradingClient
from data.data_client import DataClient, LogLevel

from models.base import AssetType
from models.watchlist import Watchlist 
from models.order import Order


CONFIG = Helper.convert_config(os.getenv("CONFIG", None))

class Trader():

    TOTAL_ALLOWED_BATCHES = 5
    STRICT_PDT = True
    OVERRIDE_ENTRY = True
    SESSION_ID = uuid.uuid4().hex

    def __init__(self, config: dict = CONFIG):
        self.bot_id = config.get("bot_id", None)
        self.bot_channel = config.get("bot_channel", None)
        # ALPACA
        self.alpaca_trading_client = AlpacaTradingClient(
            config.get("alpaca_api_key", None), 
            config.get("alpaca_api_secret_key", None), 
            config.get("alpaca_api_url_base", None),
            config.get("alpaca_data_api_url_base", None)
        )
        # COINBASE
        self.coinbase_trading_client = CoinbaseTradingClient(
            config.get("coinbase_api_key", None),
            config.get("coinbase_api_secret_key", None),
            config.get("coinbase_api_url_base", None)
        )
        self.mongo_client = DataClient(config.get("uri", None))
        self.extended_hours = False

        self.debug = config.get("debug", False)

    def client_factory(self, asset_type: AssetType) -> TradingClient:
        if asset_type == AssetType.STOCK:
            return self.alpaca_trading_client
        if asset_type == AssetType.CRYPTO:
            return self.coinbase_trading_client
        else:
            self._log(message="Invalid asset type", log_level=LogLevel.ERROR, obj={"type": asset_type})
            raise Exception("Invalid asset type")

    def _log(self, message: str, log_level: str = LogLevel.INFO, symbol: str = None, obj: dict = None):
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

        active_watchlists = [Watchlist.from_mongo(doc) for doc in self.mongo_client.read("watchlist", {"is_active": True })]

        for watchlist in active_watchlists:
            client: TradingClient = self.client_factory(watchlist.type)

            latest_bar = client.get_latest_bar(watchlist.symbol)
            last_close = float(latest_bar[watchlist.symbol]['c'])
            
            # get those orders that have not been filled
            open_orders = self.get_open_orders(watchlist.symbol, watchlist.type)

            # no open orders
            if not open_orders:
                self._log(
                    message=f"No active orders {watchlist.symbol}; running entry.", 
                    log_level=LogLevel.INFO, 
                    symbol=watchlist.symbol
                )
                self.buy(client, watchlist, watchlist.batch_size)
            else:
                self._log(
                    message=f"Active orders found {watchlist.symbol}; total orders {len(open_orders)}; running sell.", 
                    symbol=watchlist.symbol, 
                    log_level=LogLevel.INFO
                )
                # process sell criteria and execute sell if met
                sell, logs = client.process_sell(open_orders, watchlist, last_close, latest_bar)
                # log messages from process sell
                [self._log(**log) for log in logs]
                # sell orders
                [self.sell(client, watchlist, order) for order in sell]

                self.rebuy(open_orders, watchlist, last_close)

        self._log(
            message="End", 
            log_level=LogLevel.INFO
        )
        return True


    def buy(self, client: TradingClient, w: Watchlist, notional: float) -> bool:
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

            order = client.create_order(payload)
            if not order.get("status", None) == "filled":
                # sometimes the order doesn't process immediately
                order = client.get_order(w.symbol, order.get("id"))

            if order:
                # creates a new order object
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

    def sell(self, client: TradingClient, w: Watchlist, o: Order):
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
            order = client.create_order(payload)
            self._log(
                message=f"Success selling stock {w.symbol}", 
                symbol=w.symbol, 
                log_level=LogLevel.INFO, 
                obj=order
            )

            if not order.get("status", None) == "filled":
                # sometimes the order doesn't process immediately
                filled_order = client.get_order(order_id=order.get("id"))
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

    def get_open_orders(self, symbol: str, type = AssetType.STOCK) -> list[Order]:
        filter = {"symbol": symbol, "type": type, "buy_status": "filled", "sell_status": None}
        return [Order.from_mongo(doc) for doc in self.mongo_client.read("order", filter)]



if __name__ == '__main__':
    Trader(CONFIG).run()
