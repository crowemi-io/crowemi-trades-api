import unittest

from common.alpaca import alert_channel


class TestAlert(unittest.TestCase):

    def setUp(self):
        pass

    def test_get(self):
        alert_channel("Test message")


if __name__ == '__main__':
    unittest.main()