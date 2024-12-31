import json
import os
import uuid
from datetime import datetime, timedelta, UTC

from common.helper import Helper, TelegramNotifier
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
        self.data_client = DataClient(config.get("uri", None), session_id=self.SESSION_ID)
        self.notifier = TelegramNotifier(bot_id=self.bot_id, channel_id=self.bot_channel)
        # ALPACA
        self.alpaca_trading_client = AlpacaTradingClient(
            api_key=config.get("alpaca_api_key", None), 
            api_secret_key=config.get("alpaca_api_secret_key", None), 
            base_url=config.get("alpaca_api_url_base", None),
            data_base_url=config.get("alpaca_data_api_url_base", None),
            data_client=self.data_client,
            notifier=self.notifier
        )
        # COINBASE
        self.coinbase_trading_client = CoinbaseTradingClient(
            api_key=config.get("coinbase_api_key", None),
            api_secret_key=config.get("coinbase_api_secret_key", None),
            base_url=config.get("coinbase_api_url_base", None),
            data_client=self.data_client,
            notifier=self.notifier
        )
        self.extended_hours = False

        self.debug = config.get("debug", False)

    def client_factory(self, asset_type: AssetType) -> TradingClient:
        if asset_type == AssetType.STOCK.value:
            return self.alpaca_trading_client
        if asset_type == AssetType.CRYPTO.value:
            return self.coinbase_trading_client
        else:
            self.data_client.log(message="Invalid asset type", log_level=LogLevel.ERROR, obj={"type": asset_type})
            raise Exception("Invalid asset type")

    def run(self) -> bool:
        self.data_client.log(message="Start", log_level=LogLevel.INFO)
        if self.debug:
            self.data_client.log(message="Debug mode enabled", log_level=LogLevel.DEBUG)

        active_watchlists = [Watchlist.from_mongo(doc) for doc in self.data_client.read("watchlist", {"is_active": True })]

        for watchlist in active_watchlists:
            client: TradingClient = self.client_factory(watchlist.type)
            if not client.is_runnable():
                client.data_client.log(
                    message=f"{watchlist.symbol} is not runnable.", 
                    log_level=LogLevel.INFO, 
                    symbol=watchlist.symbol
                )
                continue

            # TODO: move thise to client obj
            latest_bar = client.get_latest_bar(watchlist.symbol)
            last_close = float(latest_bar[watchlist.symbol]['c'])
            
            # get those orders that have not been filled
            filter = {"symbol": watchlist.symbol, "type": watchlist.type, "buy_status": "filled", "sell_status": None}
            open_orders = [Order.from_mongo(doc) for doc in client.data_client.read("order", filter)]

            # no open orders
            if not open_orders:
                client.data_client.log(
                    message=f"No active orders {watchlist.symbol}; running entry.", 
                    log_level=LogLevel.INFO, 
                    symbol=watchlist.symbol
                )
                if client.process_buy(watchlist.symbol):
                    client.buy(watchlist)
            else:
                client.data_client.log(
                    message=f"Active orders found {watchlist.symbol}; total orders {len(open_orders)}; running sell.", 
                    symbol=watchlist.symbol, 
                    log_level=LogLevel.INFO
                )
                # process sell criteria and execute sell if met
                client.process_sell(open_orders, watchlist, last_close, latest_bar) # TODO: remove last_close, latest_bar
                client.process_rebuy(open_orders, watchlist, last_close) # TODO: remove last_close

        client.data_client.log(
            message="End", 
            log_level=LogLevel.INFO
        )
        return True

    def get_open_orders(self, symbol: str, type = AssetType.STOCK) -> list[Order]:
        filter = {"symbol": symbol, "type": type, "buy_status": "filled", "sell_status": None}
        return [Order.from_mongo(doc) for doc in self.data_client.read("order", filter)]



if __name__ == '__main__':
    Trader(CONFIG).run()
