import unittest
from data.models import Order

class TestOrder(unittest.TestCase):

    def setUp(self):
        self.order_batch = Order().get()

    def test_get(self):
        order = Order.get()
        self.assertEqual(order, None)
        
    def test_calculate_profit(self):
        order = Order(
            quantity=0.04460542,
            buy_price=224.188,
            sell_price=225.184
        )
        order.calculate_profit()
        self.assertEqual(order.profit, 0.04)

if __name__ == '__main__':
    unittest.main()