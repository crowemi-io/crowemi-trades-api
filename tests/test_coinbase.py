import unittest

from common.helper import get_local_config
from trading.coinbase_client import CoinbaseTradingClient


class TestAlpaca(unittest.TestCase):

    def setUp(self):
        self.config = get_local_config()

    def test_get_order(self):
        # get orders by symbol
        api_key = self.config.get("coinbase_api_key", None)
        api_secret_key = self.config.get("coinbase_api_secret_key", None)
        api_base_url = self.config.get("coinbase_api_url_base", None)
        coinbase_trader = CoinbaseTradingClient(api_key, api_secret_key, api_base_url)
        accounts = coinbase_trader.list_account()
        self.assertIsNotNone(accounts)

    def test_get_asset(self):
        asset = self.trader.alpaca_trading_client.get_asset("AMZN")
        self.assertIsNotNone(asset)





if __name__ == '__main__':
    unittest.main()