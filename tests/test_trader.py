import json
import unittest
from datetime import datetime, timedelta, UTC

from common.helper import Helper, get_local_config
from models.base import Order, Watchlist
from trader import Trader

class TestTrader(unittest.TestCase):

    def setUp(self):
        self.trader = Trader(get_local_config())

    def test_log(self):
        pass

    def test_process_sell(self):
        order = Order()
        order.quantity = 0.148670145

        watchlist = Watchlist(symbol="NVDA")
        self.trader.sell(watchlist, order)

    def test_open_orders(self):
        open_orders = self.trader.get_open_orders("MSTR")
        assert len(open_orders) > 0

    def test_rebuy(self):
        pass

    def test_buy(self):
        pass

    def test_sell(self):
        pass
        
    def test_avg_daily_swing(self):
        start_date = datetime.now(UTC)
        end_date = start_date - timedelta(days=60)
        bars = self.trader.alpaca_data_client.get_historical_bars("AAPL", "1D", 1000, end_date.strftime("%Y-%m-%d"), start_date.strftime("%Y-%m-%d"))
        data = {"bars": [
            {'c': 232.89, 'h': 233.24, 'l': 229.74, 'n': 10483, 'o': 231.49, 't': '2024-11-25T05:00:00Z', 'v': 860206, 'vw': 231.678886},
            {'c': 229.75, 'h': 230.71, 'l': 228.175, 'n': 9155, 'o': 228.23, 't': '2024-11-22T05:00:00Z', 'v': 827598, 'vw': 229.656916},
            {'c': 228.48, 'h': 230.13, 'l': 225.72, 'n': 11131, 'o': 228.785, 't': '2024-11-21T05:00:00Z', 'v': 985294, 'vw': 228.337011},
            {'c': 228.21, 'h': 230.16, 'l': 226.73, 'n': 8190, 'o': 226.74, 't': '2024-11-19T05:00:00Z', 'v': 632129, 'vw': 228.731541},
            {'c': 228.16, 'h': 229.735, 'l': 225.17, 'n': 10442, 'o': 225.3, 't': '2024-11-18T05:00:00Z', 'v': 719007, 'vw': 228.004347},
            {'c': 224.95, 'h': 226.88, 'l': 224.28, 'n': 10234, 'o': 225.92, 't': '2024-11-15T05:00:00Z', 'v': 742110, 'vw': 224.976987}
        ]}
        a = Helper.process_bar(data, 5)
        assert round(a["avg_daily_swing"],2) == 3.69

    def test_backfill(self):
        has_missing = self.trader.backfill()
        self.assertFalse(has_missing)


if __name__ == '__main__':
    unittest.main()