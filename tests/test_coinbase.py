import unittest

from common.helper import get_local_config

from trading.coinbase_client import CoinbaseTradingClient


class TestCoinbase(unittest.TestCase):

    def setUp(self):
        self.config = get_local_config()
        
        self.client = CoinbaseTradingClient(
            self.config.get("coinbase_api_key", None), 
            self.config.get("coinbase_api_secret_key", None), 
            self.config.get("coinbase_api_url_base", None)
        )

    # GET api.coinbase.com/api/v3/brokerage/accounts

    def test_list_orders(self):
        # get orders by symbol
        orders = self.client.list_orders()
        self.assertIsNotNone(orders)

    def test_list_assets(self):
        asset = self.client.list_accounts()
        self.assertIsNotNone(asset)

    def test_get_orders(self):
        pass





if __name__ == '__main__':
    unittest.main()