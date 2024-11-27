import unittest

from common.helper import get_local_config
from trader import Trader


class TestAlpaca(unittest.TestCase):

    def setUp(self):
        self.trader = Trader(get_local_config())        

    def test_get_order(self):
        # get orders by symbol
        orders = self.trader.trading_client.get_order("AAPL")
        self.assertGreater(len(orders), 0)
        # get all orders
        orders = self.trader.trading_client.get_order()
        self.assertGreater(len(orders), 0)





if __name__ == '__main__':
    unittest.main()