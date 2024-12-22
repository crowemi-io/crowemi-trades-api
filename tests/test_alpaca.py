import unittest

from common.helper import get_local_config

from trading.alpaca_client import AlpacaTradingClient
from data.data_client import DataClient


class TestAlpaca(unittest.TestCase):

    def setUp(self):
        config = get_local_config()
        self.client = AlpacaTradingClient(
            api_key=config.get("alpaca_api_key", None),
            api_secret_key=config.get("alpaca_api_secret_key", None),
            base_url=config.get("alpaca_api_url_base", None),
            data_base_url=config.get("alpaca_data_api_url_base", None),
            data_client=DataClient(config.get("uri", None))
        )

    def test_process_sell(self):
        pass

    def test_is_runnable(self):
        pass

    def test_process_buy(self):
        pass

    def test_buy(self):
        pass

    def test_sell(self):
        pass

    def test_create_order_obj(self):
        pass

    def test_get_order(self):
        # get orders by symbol
        orders = self.client.get_order("AAPL")
        self.assertGreater(len(orders), 0)
        # get all orders
        orders = self.client.get_order()
        self.assertGreater(len(orders), 0)

    def test_get_asset(self):
        asset = self.client.get_asset("AMZN")
        self.assertIsNotNone(asset)

    def test_get_latest_bar(self):
        asset = self.client.get_latest_bar("AMZN")
        self.assertIsNotNone(asset)



if __name__ == '__main__':
    unittest.main()