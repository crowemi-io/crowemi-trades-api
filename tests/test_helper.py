import unittest

from datetime import datetime, timedelta, UTC

from common.helper import get_local_config, Helper
from trading.alpaca_client import AlpacaTradingClient
from data.data_client import DataClient


class TestHelper(unittest.TestCase):

    def setUp(self):
        config = get_local_config()
        self.client = AlpacaTradingClient(
            api_key=config.get("alpaca_api_key", None),
            api_secret_key=config.get("alpaca_api_secret_key", None),
            base_url=config.get("alpaca_api_url_base", None),
            data_base_url=config.get("alpaca_data_api_url_base", None),
            data_client=DataClient(config.get("uri", None))
        )

    def test_process_bars(self):
        bars = {"bars": [
            {'c': 232.89, 'h': 233.24, 'l': 229.74, 'n': 10483, 'o': 231.49, 't': '2024-11-25T05:00:00Z', 'v': 860206, 'vw': 231.678886},
            {'c': 229.75, 'h': 230.71, 'l': 228.175, 'n': 9155, 'o': 228.23, 't': '2024-11-22T05:00:00Z', 'v': 827598, 'vw': 229.656916},
            {'c': 228.48, 'h': 230.13, 'l': 225.72, 'n': 11131, 'o': 228.785, 't': '2024-11-21T05:00:00Z', 'v': 985294, 'vw': 228.337011},
            {'c': 228.21, 'h': 230.16, 'l': 226.73, 'n': 8190, 'o': 226.74, 't': '2024-11-19T05:00:00Z', 'v': 632129, 'vw': 228.731541},
            {'c': 228.16, 'h': 229.735, 'l': 225.17, 'n': 10442, 'o': 225.3, 't': '2024-11-18T05:00:00Z', 'v': 719007, 'vw': 228.004347},
            {'c': 224.95, 'h': 226.88, 'l': 224.28, 'n': 10234, 'o': 225.92, 't': '2024-11-15T05:00:00Z', 'v': 742110, 'vw': 224.976987}
        ]}
        end_date = datetime.now(UTC) # we want today minus thirty days for the calculation
        start_date = end_date - timedelta(days=90)
        # gets the historical bars for calculating the average daily swing
        bars = self.client.get_historical_bars("MSFT", "1D", 1000, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        ret = Helper.process_bar(bars, 7)
        self.assertTrue(ret["avg_daily_swing"] > 0)
        
        